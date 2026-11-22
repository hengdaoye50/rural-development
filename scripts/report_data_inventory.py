# -*- coding: utf-8 -*-
"""数据集清单：一次性把「库里有什么、口径怎么分」打印成可读报告（只读）。

前端要什么，先要清楚库里有哪些表/视图、每张多少行、关键分布长什么样。
本脚本不写库，只读 `data/db/片区库.sqlite3`，输出 `reports/qa/数据清单-{date}.md`。

用法：
  python scripts/report_data_inventory.py
  python scripts/report_data_inventory.py --out reports/qa/xxx.md
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)


def q(con, sql, args=()):
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(sql, args)]


def one(con, sql, args=(), default=0):
    rows = q(con, sql, args)
    if not rows:
        return default
    v = list(rows[0].values())[0]
    return v if v is not None else default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    out = Path(args.out) if args.out else ROOT / "reports" / "qa" / f"数据清单-{date.today()}.md"

    L: list[str] = []
    add = L.append

    add(f"# 数据集清单（只读盘点）\n\n> 库：`{DB.relative_to(ROOT).as_posix()}`｜生成：{date.today()}\n")

    # 1. 表 / 视图
    add("## 一、表与视图\n")
    add("| 类型 | 名称 | 行数 |")
    add("|---|---|---|")
    objs = q(con, "select name, type from sqlite_master where type in ('table','view') "
                  "and name not like 'sqlite_%' order by type desc, name")
    for o in objs:
        n = one(con, f"select count(*) from `{o['name']}`")
        add(f"| {o['type']} | `{o['name']}` | {n:,} |")
    add("")

    # 2. 口径分层
    add("## 二、口径分层（视图 `area_caliber`）\n")
    rows = q(con, "select caliber_group grp, count(*) n from area_caliber where in_scope=1 group by 1 order by 1")
    total = sum(r["n"] for r in rows)
    add("| 组 | 数量 | 说明 |")
    add("|---|---|---|")
    desc = {"A": "窗内成立且有依据", "B": "2022 前成立但延续至今", "C": "时间不详",
            "D": "口径外（2022 前且未延续）", "E": "无 primary/support 依据"}
    for r in rows:
        add(f"| {r['grp']} | {r['n']:,} | {desc.get(r['grp'], '')} |")
    add(f"| 合计 | {total:,} | 在册口径内 |")
    add("")
    main_n = one(con, "select count(*) from area_caliber where in_main_stat=1")
    wide_n = one(con, "select count(*) from area_caliber where in_scope=1 and caliber_group in ('A','B','C')")
    pend_n = one(con, "select count(*) from area where status='待核' and record_state='active'")
    area_n = one(con, "select count(*) from area where record_state='active'")
    belt_n = one(con, "select count(*) from belt")
    add(f"- 主统计 A+B：**{main_n:,}**｜宽统计 A+B+C：**{wide_n:,}**｜待核：**{pend_n:,}**")
    add(f"- 宏观层 M（`macro_unit`）：**{one(con, 'select count(*) from macro_unit'):,}**"
        f"（area {area_n:,} + belt {belt_n:,}，去跨表重名）\n")

    # 3. 分省
    add("## 三、分省（M 层 / 主统计 / 待核 / 覆盖县数）\n")
    add("| 省 | M 层 | 主统计 | 待核 | 覆盖县 |")
    add("|---|---|---|---|---|")
    prov = q(con, """
        select p.province_code,
               (select count(*) from macro_unit m where m.province_code=p.province_code) m,
               (select count(*) from area_caliber c join area a on a.area_id=c.area_id
                 where c.in_main_stat=1 and a.province_code=p.province_code) main,
               (select count(*) from area a where a.province_code=p.province_code
                 and a.status='待核' and a.record_state='active') pend,
               (select count(distinct county_code) from area a where a.province_code=p.province_code
                 and a.record_state='active') cnt
        from (select distinct province_code from area) p order by m desc""")
    for r in prov:
        add(f"| {r['province_code']} | {r['m']:,} | {r['main']:,} | {r['pend']:,} | {r['cnt']:,} |")
    add("")

    # 4. 时间 / 类型 / 设立方式
    add("## 四、主统计的结构分布\n")
    add("### 4.1 成立年份\n")
    add("| 年 | 数量 |")
    add("|---|---|")
    for r in q(con, """select substr(a.founded_ymd,1,4) y, count(*) n
                       from area_caliber c join area a on a.area_id=c.area_id
                       where c.in_main_stat=1 group by 1 order by 1"""):
        add(f"| {r['y'] or '(空)'} | {r['n']:,} |")
    add("")
    add("### 4.2 类型 `type_code`\n")
    add("| 类型 | 主统计 | 全量在册 |")
    add("|---|---|---|")
    for r in q(con, """select a.type_code t,
                         sum(case when c.in_main_stat=1 then 1 else 0 end) main,
                         count(*) all_n
                       from area a left join area_caliber c on c.area_id=a.area_id
                       where a.record_state='active' group by 1 order by all_n desc"""):
        add(f"| {r['t']} | {r['main']:,} | {r['all_n']:,} |")
    add("")
    add("### 4.3 设立方式 `setup_kind`（主统计）\n")
    add("| setup_kind | 数量 |")
    add("|---|---|")
    for r in q(con, """select coalesce(nullif(a.setup_kind,''),'unknown') k, count(*) n
                       from area_caliber c join area a on a.area_id=c.area_id
                       where c.in_main_stat=1 group by 1 order by n desc"""):
        add(f"| {r['k']} | {r['n']:,} |")
    add("")
    add("### 4.4 层级（`agency_level` / `admin_level`）\n")
    add("| agency_level | 数量 |")
    add("|---|---|")
    for r in q(con, """select coalesce(nullif(agency_level,''),'unknown') k, count(*) n
                       from area where record_state='active' group by 1 order by n desc"""):
        add(f"| {r['k']} | {r['n']:,} |")
    add("")

    # 5. 证据
    add("## 五、证据链\n")
    ev = q(con, """select
        sum(case when exists(select 1 from area_policy_map m where m.area_id=a.area_id and m.rel in ('primary','support')) then 1 else 0 end) hard,
        sum(case when exists(select 1 from area_policy_map m where m.area_id=a.area_id and m.rel='mention') then 1 else 0 end) mention,
        sum(case when not exists(select 1 from area_policy_map m where m.area_id=a.area_id) then 1 else 0 end) nopolicy
        from area a where a.record_state='active'""")[0]
    add(f"- 有 primary/support：**{ev['hard']:,}**｜仅 mention：**{ev['mention']:,}**｜无政策挂接：**{ev['nopolicy']:,}**")
    add(f"- `policy`：{one(con, 'select count(*) from policy'):,} 份｜全文 {one(con, 'select sum(full_text_chars) from policy'):,} 汉字")
    add(f"- `source`：{one(con, 'select count(*) from source'):,} 条｜`area_source_map`：{one(con, 'select count(*) from area_source_map'):,} 条")
    add("")
    add("| policy.source_kind | 数量 |")
    add("|---|---|")
    for r in q(con, "select coalesce(nullif(source_kind,''),'(空)') k, count(*) n from policy group by 1 order by n desc"):
        add(f"| {r['k']} | {r['n']:,} |")
    add("")

    # 6. 台账
    add("## 六、三份台账\n")
    for table, key in (("province_roster", "province_code"), ("city_roster", "city_code"), ("county_roster", "county_code")):
        try:
            rows = q(con, f"select status, count(*) n from {table} group by 1 order by n desc")
        except sqlite3.Error:
            add(f"- `{table}`：不存在\n")
            continue
        add(f"- `{table}`：" + "｜".join(f"{r['status']} {r['n']}" for r in rows))
    add("")

    # 7. 县级覆盖
    add("## 七、县覆盖\n")
    tot = one(con, "select count(*) from region where level='county'")
    cov_map = one(con, """select count(distinct m.region_code) from area_region_map m
                          join area a on a.area_id=m.area_id where a.record_state='active'""")
    cov_col = one(con, "select count(distinct county_code) from area where record_state='active'")
    add(f"- 县级单位（region）：**{tot:,}**")
    add(f"- 有在册片区（按 area.county_code）：**{cov_col:,}**（{cov_col / tot * 100:.1f}%）")
    add(f"- 有在册片区（按 area_region_map）：**{cov_map:,}**（{cov_map / tot * 100:.1f}%）")
    add("- 两个口径必须并列报，差异来自「归属行缺失/功能区记市级码」\n")

    add("## 八、前端可直接用的取数入口\n")
    add("- 总量/分层：`area_caliber`（`in_scope` / `in_main_stat` / `caliber_group`）")
    add("- 命名单元：`macro_unit`（area+belt 去重，含省/市/县/年/证据强度）")
    add("- 一行一区：`v_analysis_area`（含省名/县名/层级/证据/政策数）")
    add("- 台账：`province_roster` / `city_roster` / `county_roster` / `evidence_debt`")
    add("- 导出：`scripts/export_web_data.py` → `web/data.js`\n")

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(out)
    print(f"OK -> {out.relative_to(ROOT)}")
    print("M %d | 主统计 %d | 待核 %d" % (
        one(con, "select count(*) from macro_unit"),
        one(con, "select count(*) from area_caliber where in_main_stat=1"),
        one(con, "select count(*) from area where status='待核' and record_state='active'")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
