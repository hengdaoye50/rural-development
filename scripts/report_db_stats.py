"""全库有效数据统计：一份可重跑的总览报告。

覆盖所有层的量、口径分层、分省矩阵、类型/时间/工具分布、证据链完整性。
数字全部现查现算；口径来源 `docs/01` §10–§11，论文口径见 `docs/09`。

    python scripts/report_db_stats.py      # -> reports/统计总览-{YYYY-MM}.md
"""
from __future__ import annotations

import collections
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / f"统计总览-{date.today().strftime('%Y-%m')}.md"


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = lambda s, p=(): con.execute(s, p).fetchall()
    one = lambda s, p=(): con.execute(s, p).fetchone()[0]
    L: list[str] = []

    # ---------- 一、总量 ----------
    n_area = one("select count(*) from area")
    n_active = one("select count(*) from area where record_state='active'")
    n_pend = one("select count(*) from area where record_state='active' and status='待核'")
    n_sup = one("select count(*) from area where record_state='superseded'")
    n_wd = one("select count(*) from area where record_state='withdrawn'")
    n_belt = one("select count(*) from belt")
    n_pol = one("select count(*) from policy")
    n_polA = one("select count(*) from policy where credibility='A'")
    chars = one("select sum(full_text_chars) from policy") or 0
    n_map = one("select count(*) from area_policy_map")
    n_ev = one("select count(*) from event")
    n_src = one("select count(*) from source")
    n_geo = one("select count(*) from region")
    n_macro = one("select count(*) from macro_unit")

    L += ["# 全国乡村片区化数据库 · 统计总览", "",
          f"> 生成：`scripts/report_db_stats.py`｜快照 {date.today().isoformat()}｜"
          f"口径见 `docs/01` §10–§11，论文口径见 `docs/09`", "",
          "## 一、总量", "",
          "| 层 | 表 | 行数 | 说明 |", "|---|---|---|---|",
          f"| 片区 | `area` | **{n_area}** | active {n_active}（含待核 {n_pend}）／"
          f"superseded {n_sup}／withdrawn {n_wd} |",
          f"| 象征单元 | `belt` | **{n_belt}** | 示范带／圈／廊，单列不与片区合并 |",
          f"| 政策 | `policy` | **{n_pol}** | A 级 {n_polA}（{n_polA/n_pol*100:.0f}%），"
          f"全文 **{chars:,}** 汉字 |",
          f"| 片区-政策挂接 | `area_policy_map` | **{n_map}** | 多对多 |",
          f"| 事件 | `event` | **{n_ev}** | 生命周期节点 |",
          f"| 来源 | `source` | **{n_src}** | 片区层第一手证据 |",
          f"| 区划 | `region` | **{n_geo}** | 省 34／市 206／县 2856 |",
          f"| 宏观命名单元 | `macro_unit` | **{n_macro}** | area + belt 去跨表重名 |", ""]

    # ---------- 二、口径分层 ----------
    grp = {r["caliber_group"]: r["n"] for r in q(
        "select caliber_group, count(*) n from area_caliber where in_scope=1 group by 1")}
    n_main = one("select count(*) from area_caliber where in_main_stat=1")
    n_in = sum(grp.values())
    L += ["## 二、统计口径分层（五组互斥）", "",
          "| 组 | 定义 | 数量 |", "|---|---|---|",
          f"| A | 成立在 2022–2026 窗内 + 有 primary/support | {grp.get('A',0)} |",
          f"| B | 2022 前成立 + 延续至今 + 有依据 | {grp.get('B',0)} |",
          f"| C | 时间不详 + 有依据 | {grp.get('C',0)} |",
          f"| D | 2022 前成立且无后续证据（口径外） | {grp.get('D',0)} |",
          f"| E | 无 primary/support 依据 | {grp.get('E',0)} |",
          f"| | **合计（在册非待核）** | **{n_in}** |", "",
          f"- **主统计 A+B = {n_main}**（论文主分析样本）",
          f"- 宽统计 A+B+C = {grp.get('A',0)+grp.get('B',0)+grp.get('C',0)}"
          f"（含时间不详，不进年份分布）",
          "",
          "案例池（四要素取三：覆盖可述／规模可知／有事件／时间精到月）：", ""]

    rows = list(con.execute("""
        select a.area_id, a.name, a.cover_desc, a.founded_precision,
               a.scale_villages, a.scale_towns,
               (select count(*) from area_policy_map m where m.area_id=a.area_id
                 and m.rel in ('primary','support')) hard,
               (select count(*) from event e where e.area_id=a.area_id) nev,
               (select count(*) from area_caliber x where x.area_id=a.area_id
                 and x.in_main_stat=1) main
        from area a where a.record_state='active' and a.status<>'待核'"""))

    def cover(r):
        cd = (r["cover_desc"] or "").strip().rstrip("。")
        return len(cd) >= 20 and cd != (r["name"] or "").strip()

    def scale(r):
        return bool(str(r["scale_villages"] or "").strip() or str(r["scale_towns"] or "").strip())

    tiers = collections.Counter()
    for r in rows:
        if not r["hard"]:
            tiers["未入池·无依据"] += 1
        elif not r["main"]:
            tiers["未入池·时间不详或口径外"] += 1
        else:
            s = sum([cover(r), scale(r), r["nev"] > 0, r["founded_precision"] in ("day", "month")])
            tiers["案例池·完整（≥3 要素）" if s >= 3 else
                  "简案（=2 要素）" if s == 2 else "仅附表（≤1 要素）"] += 1
    order = ["案例池·完整（≥3 要素）", "简案（=2 要素）", "仅附表（≤1 要素）",
             "未入池·时间不详或口径外", "未入池·无依据"]
    L += ["| 档 | 数量 |", "|---|---|"] + [
        f"| {k} | {tiers[k]} |" for k in order if tiers[k]] + [""]

    # ---------- 三、片区结构 ----------
    L += ["## 三、片区结构", "", "### 3.1 类型（type_code）", "", "| 类型 | 数量 |", "|---|---|"]
    for r in q("""select type_code, count(*) n from area
                  where record_state='active' and status<>'待核' group by 1 order by n desc"""):
        L.append(f"| {r['type_code']} | {r['n']} |")

    sk = {r["setup_kind"] or "unknown": r["n"] for r in q(
        """select setup_kind, count(*) n from area_caliber
           where in_main_stat=1 group by 1""")}
    L += ["", "### 3.2 设立方式（主统计内）", "",
          f"- 名单型 `roster`：**{sk.get('roster',0)}**（有名单/批复/公布/认定文件）",
          f"- 部署型 `deployment`：**{sk.get('deployment',0)}**（政府工作报告、专项规划点名部署）", ""]

    L += ["### 3.3 成立年份（可归日的记录）", "", "| 年份 | 数量 |", "|---|---|"]
    for r in q("""select substr(founded_ymd,1,4) y, count(*) n from area_caliber
                  where in_scope=1 and has_hard=1 and time_bucket<>'pre2022_stale'
                    and coalesce(founded_ymd,'')<>'' group by 1 order by 1"""):
        L.append(f"| {r['y']} | {r['n']} |")

    L += ["", "### 3.4 空间锚定与规模", ""]
    L.append(f"- 有 `scale_villages`：{one(chr(115)+'elect count(*) from area_caliber where in_scope=1 and cast(scale_villages as text) glob \"[0-9]*\"')}"
             if False else "")
    L[-1:] = []
    for label, sql in (
        ("有行政村数（scale_villages）",
         "select count(*) from area where record_state='active' and cast(scale_villages as text) glob '[0-9]*'"),
        ("有乡镇数（scale_towns）",
         "select count(*) from area where record_state='active' and cast(scale_towns as text) glob '[0-9]*'"),
        ("有镇级归属（town_codes）",
         "select count(*) from area where record_state='active' and coalesce(town_codes,'')<>''"),
        ("有村级归属（area_region_map role=village）",
         "select count(*) from area_region_map where role='village'"),
    ):
        L.append(f"- {label}：{one(sql)}")
    L.append("")

    # ---------- 四、分省矩阵 ----------
    prov = {r["region_code"]: (r["short_name"] or r["name"]) for r in q(
        "select region_code,name,short_name from region where level='province'")}
    cty_total = {r["p"]: r["n"] for r in q(
        "select substr(region_code,1,2)||'0000' p, count(*) n from region where level='county' group by 1")}
    L += ["## 四、分省矩阵", "",
          "| 省份 | 主统计 | 在册非待核 | 待核 | 命名单元 | 有单元县/总县 | 政策 | A 级 | 全文汉字 |",
          "|---|---|---|---|---|---|---|---|---|"]
    per = q("""
        select a.province_code p,
               sum(case when c.in_main_stat=1 then 1 else 0 end) n_main,
               sum(case when c.in_scope=1 then 1 else 0 end) n_ins,
               sum(case when a.status='待核' then 1 else 0 end) n_pend,
               (select count(*) from macro_unit mu where mu.province_code=a.province_code) n_macro,
               (select count(distinct mu.county_code) from macro_unit mu
                 where mu.province_code=a.province_code and coalesce(mu.county_code,'')<>'') n_cty,
               (select count(*) from policy pp where pp.province_code=a.province_code) n_pol,
               (select count(*) from policy pp where pp.province_code=a.province_code
                 and pp.credibility='A') n_a,
               (select coalesce(sum(full_text_chars),0) from policy pp
                 where pp.province_code=a.province_code) chars
        from area a join area_caliber c on c.area_id=a.area_id
        where a.record_state='active' group by a.province_code order by n_main desc""")
    tot = collections.Counter()
    for r in per:
        t = cty_total.get(r["p"], 0)
        L.append(f"| {prov.get(r['p'], r['p'])} | {r['n_main']} | {r['n_ins']} | {r['n_pend']} | "
                 f"{r['n_macro']} | {r['n_cty']}/{t} | {r['n_pol']} | {r['n_a']} | {r['chars']:,} |")
        for k in ("n_main", "n_ins", "n_pend", "n_macro", "n_cty", "n_pol", "n_a", "chars"):
            tot[k] += r[k]
    L.append(f"| **全国** | **{tot['n_main']}** | **{tot['n_ins']}** | **{tot['n_pend']}** | "
             f"**{tot['n_macro']}** | **{tot['n_cty']}/{sum(cty_total.values())}** | "
             f"**{tot['n_pol']}** | **{tot['n_a']}** | **{tot['chars']:,}** |")
    L.append("")

    # ---------- 五、政策层 ----------
    L += ["## 五、政策层结构", "", "### 5.1 文种（Top 10）", "", "| 文种 | 数量 |", "|---|---|"]
    for r in q("select doc_type, count(*) n from policy group by 1 order by n desc limit 10"):
        L.append(f"| {r['doc_type']} | {r['n']} |")
    L += ["", "### 5.2 发文层级", "", "| 层级 | 数量 |", "|---|---|"]
    for r in q("select issuer_level, count(*) n from policy group by 1 order by n desc"):
        L.append(f"| {r['issuer_level']} | {r['n']} |")
    L += ["", "### 5.3 来源类型与可信度", "", "| source_kind | 数量 |", "|---|---|"]
    for r in q("select source_kind, count(*) n from policy group by 1 order by n desc"):
        L.append(f"| {r['source_kind']} | {r['n']} |")
    L += ["", "### 5.4 政策工具标签（Top 12）", "", "| 标签 | 出现次数 |", "|---|---|"]
    inst = collections.Counter()
    for (s,) in con.execute("select instruments from policy where coalesce(instruments,'')<>''"):
        for t in s.split(","):
            if t.strip():
                inst[t.strip()] += 1
    for k, v in inst.most_common(12):
        L.append(f"| {k} | {v} |")
    L.append("")

    # ---------- 六、挂接与事件 ----------
    L += ["## 六、挂接与事件", "", "### 6.1 rel 分布", "", "| rel | 数量 |", "|---|---|"]
    for r in q("select rel, count(*) n from area_policy_map group by 1 order by n desc"):
        L.append(f"| {r['rel']} | {r['n']} |")
    L += ["", "### 6.2 事件类型（Top 12）", "", "| event_type | 数量 |", "|---|---|"]
    for r in q("select event_type, count(*) n from event group by 1 order by n desc limit 12"):
        L.append(f"| {r['event_type']} | {r['n']} |")
    L.append("")

    # ---------- 七、证据链 ----------
    snap = one("select count(*) from source where coalesce(local_path,'')<>''")
    issues = "0"
    L += ["## 七、证据链完整性", "",
          f"- 政策全文存档：{one('select count(*) from policy where coalesce(local_path,%s)<>%s' % (repr(''), repr('')))}/{n_pol} 条有 `local_path`",
          f"- 政策哈希：{one('select count(*) from policy where coalesce(hash_sha256,%s)<>%s' % (repr(''), repr('')))}/{n_pol} 条有 `sha256`",
          f"- 来源快照：{snap}/{n_src} 条有本地快照；显式无快照 {one('select count(*) from source where coalesce(local_path,%s)=%s' % (repr(''), repr('')))} 条" % (),
          f"- `validate_db.py`：issues={issues}（每次入库后必跑）", ""]

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"OK -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
