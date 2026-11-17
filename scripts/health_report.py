"""项目健康度总览：把散落各处的进度与质量信号汇总成一份报告。

只读，不改任何数据。输出 reports/qa/health-latest.md。

用法：
  python scripts/health_report.py
  python scripts/health_report.py --md reports/健康度.md
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "qa" / "health-latest.md"

PROV = {
    "110000": "北京", "120000": "天津", "130000": "河北", "140000": "山西", "150000": "内蒙古",
    "210000": "辽宁", "220000": "吉林", "230000": "黑龙江", "310000": "上海", "320000": "江苏",
    "330000": "浙江", "340000": "安徽", "350000": "福建", "360000": "江西", "370000": "山东",
    "410000": "河南", "420000": "湖北", "430000": "湖南", "440000": "广东", "450000": "广西",
    "460000": "海南", "500000": "重庆", "510000": "四川", "520000": "贵州", "530000": "云南",
    "540000": "西藏", "610000": "陕西", "620000": "甘肃", "630000": "青海", "640000": "宁夏",
    "650000": "新疆",
}


def main() -> int:
    args = sys.argv[1:]
    out = Path(args[args.index("--md") + 1]) if "--md" in args else OUT
    if not DB.exists():
        print(f"DB 不存在: {DB}")
        return 1

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    q = lambda s: cur.fetchone() if False else cur.execute(s).fetchone()[0]  # noqa: E731

    L: list[str] = []
    add = L.append

    add(f"# 项目健康度总览\n")
    add(f"> 生成时间：{date.today().isoformat()}｜数据库：`data/db/片区库.sqlite3`\n")

    # ---------- 一、片区层 ----------
    # docs/01：status=待核 的记录统计默认排除——它们证据链不达标（如唯一来源是媒体稿）
    VALID = "record_state='active' and status != '待核'"
    VALID_A = "a.record_state='active' and a.status != '待核'"
    n_area = q(f"select count(*) from area where {VALID}")
    n_belt = q("select count(*) from belt where record_state='active'")
    n_cty = q(f"select count(distinct county_code) from area where {VALID}")
    n_sup = q("select count(*) from area where record_state='superseded'")
    n_pending = q("select count(*) from area where record_state='active' and status='待核'")
    add("## 一、片区层\n")
    add(f"- 片区 `area`：**{n_area}** 个，覆盖 **{n_cty}** 个县（区）")
    add(f"- 象征性单元 `belt`：**{n_belt}** 个")
    if n_pending:
        add(f"- 另有 **{n_pending}** 条 `status=待核` 不计入上述口径与覆盖率"
            f"（证据链不达标，如唯一来源为媒体稿，待补 .gov.cn 官方依据）")
    if n_sup:
        add(f"- 另有 {n_sup} 条 `record_state=superseded` 的历史记录不计入上述口径"
            f"（`validate_db.py` 报的行数含它们，故与本节差 {n_sup}）")

    # ---------- 二、政策层 ----------
    n_pol = q("select count(*) from policy")
    n_a = q("select count(*) from policy where credibility='A'")
    n_chars = q("select sum(full_text_chars) from policy") or 0
    n_map = q("select count(*) from area_policy_map")
    n_covered = q(
        "select count(distinct area_id) from area_policy_map "
        f"where entity_type='area' and area_id in (select area_id from area where {VALID})"
    )
    n_cty_covered = q(
        f"""select count(distinct a.county_code) from area a
            where {VALID_A}
              and exists (select 1 from area_policy_map m
                          where m.area_id=a.area_id and m.entity_type='area')"""
    )
    add("\n## 二、政策层\n")
    add(f"- 政策 `policy`：**{n_pol}** 份（A 级 {n_a} 份，{n_a / n_pol * 100:.0f}%）" if n_pol else "- 政策：0 份")
    add(f"- 全文总量：**{n_chars:,}** 汉字")
    add(f"- 片区-政策挂接：**{n_map}** 条")
    add(f"- 有政策依据的片区：**{n_covered}/{n_area}**（{n_covered / n_area * 100:.1f}%）")
    add(f"- 有政策依据的县：**{n_cty_covered}/{n_cty}**（{n_cty_covered / n_cty * 100:.1f}%）")

    add("\n### 分省进度\n")
    add("| 省份 | 片区 | 有政策依据的片区 | 政策数 | A 级 | 全文汉字 |")
    add("|---|---|---|---|---|---|")
    rows = cur.execute(
        """select a.province_code p,
                  count(distinct a.area_id) n_area,
                  count(distinct case when m.area_id is not null then a.area_id end) n_cov,
                  (select count(*) from policy pp where pp.province_code=a.province_code) n_pol,
                  (select count(*) from policy pp where pp.province_code=a.province_code and pp.credibility='A') n_a,
                  (select coalesce(sum(full_text_chars),0) from policy pp where pp.province_code=a.province_code) chars
           from area a
           left join area_policy_map m on m.area_id=a.area_id and m.entity_type='area'
           where a.record_state='active' and a.status != '待核'
           group by a.province_code order by n_area desc"""
    ).fetchall()
    for r in rows:
        pct = r["n_cov"] / r["n_area"] * 100 if r["n_area"] else 0
        add(f"| {PROV.get(r['p'], r['p'])} | {r['n_area']} | {r['n_cov']}（{pct:.0f}%） | "
            f"{r['n_pol']} | {r['n_a']} | {r['chars']:,} |")

    add("\n### 文种分布\n")
    dt = cur.execute("select doc_type, count(*) n from policy group by doc_type order by n desc").fetchall()
    add("| 文种 | 数量 |")
    add("|---|---|")
    for r in dt:
        add(f"| {r['doc_type']} | {r['n']} |")

    add("\n### 政策工具标签 Top 15\n")
    inst = Counter()
    for (s,) in cur.execute("select instruments from policy where instruments is not null and instruments<>''"):
        for t in s.split(","):
            t = t.strip()
            if t:
                inst[t] += 1
    add("| 标签 | 出现次数 |")
    add("|---|---|")
    for k, v in inst.most_common(15):
        add(f"| {k} | {v} |")

    # ---------- 三、来源层 ----------
    src = list(cur.execute("select source_id, local_path, hash_sha256, credibility from source"))
    n_src = len(src)
    ok = [r for r in src if r["local_path"] and os.path.exists(r["local_path"])]
    broken = [r for r in src if r["local_path"] and not os.path.exists(r["local_path"])]
    nosnap = [r for r in src if not r["local_path"]]
    hashed = [r for r in ok if r["hash_sha256"]]
    mism = 0
    for r in hashed:
        try:
            if hashlib.sha256(Path(r["local_path"]).read_bytes()).hexdigest() != r["hash_sha256"]:
                mism += 1
        except OSError:
            pass
    add("\n## 三、来源层（证据链完整性）\n")
    add(f"- 来源 `source`：**{n_src}** 条")
    add(f"- 快照有效：**{len(ok)}**（{len(ok) / n_src * 100:.1f}%），其中有哈希 {len(hashed)}")
    add(f"- 断链（路径存在但文件缺失）：**{len(broken)}**")
    add(f"- 显式标记无快照（`local_path` 空）：**{len(nosnap)}**")
    if mism:
        add(f"- ⚠ 哈希与实际内容不符：**{mism}** 条，需复核")

    # ---------- 四、采集进度 ----------
    add("\n## 四、采集进度（分片）\n")
    allsh = {Path(p).name.replace("-brief.md", "") for p in glob.glob(str(ROOT / "data/stage/shards/*-brief.md"))}
    have = set()
    for p in glob.glob(str(ROOT / "data/stage/batches/POL-*.jsonl")):
        have.add(Path(p).name.replace("POL-", "").replace("-policy.jsonl", ""))
    add(f"- 分片总数：**{len(allsh)}**，已产出：**{len(allsh & have)}**，"
        f"零产出：**{len(allsh - have)}**")
    if allsh - have:
        add(f"- 零产出分片：{' '.join(sorted(allsh - have))}")

    # ---------- 五、待处理 ----------
    add("\n## 五、待处理信号\n")
    signals = []
    if broken:
        signals.append(f"断链 {len(broken)} 条（跑 `repair_source_snapshots.py`）")
    if mism:
        signals.append(f"哈希不符 {mism} 条（需人工复核）")
    warn_file = ROOT / "reports" / "qa" / "validate-latest.md"
    if warn_file.exists():
        s = warn_file.read_text(encoding="utf-8")
        for line in s.splitlines():
            if line.startswith("- warnings:"):
                signals.append(f"校验警告 {line.split(':')[1].strip()} 条（多为开放词表的非预设取值，非错误）")
                break
    name_audit = ROOT / "reports" / "qa" / "area-name-audit.csv"
    if name_audit.exists():
        drift = sum(1 for r in csv.DictReader(name_audit.open(encoding="utf-8-sig"))
                    if r.get("status") == "疑似漂移")
        if drift:
            signals.append(f"片区名称疑似漂移 {drift} 条（见 `reports/qa/area-name-audit.csv`）")
    add("\n".join(f"- {x}" for x in signals) if signals else "- 无阻断性问题")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L[:28]))
    print(f"\n... -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
