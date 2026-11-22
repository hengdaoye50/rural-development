# -*- coding: utf-8 -*-
"""列出 2022 年及以前成立的片区，并标注可疑点（只读）。

输出：
  reports/qa/2022及以前成立片区-清单.md
  reports/qa/2022及以前成立片区-清单.csv
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT_MD = ROOT / "reports" / "qa" / "2022及以前成立片区-清单.md"
OUT_CSV = ROOT / "reports" / "qa" / "2022及以前成立片区-清单.csv"

CAL = {"A": "A 窗内", "B": "B 延续至今", "C": "C 时间不详", "D": "D 口径外", "E": "E 无依据"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    regions = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    rows = []
    for a in con.execute("""
        select a.area_id, a.name, a.province_code, a.city_code, a.county_code,
               a.founded_ymd, a.founded_precision, a.status, a.type_code, a.setup_kind,
               a.cover_desc, a.summary, a.issuer,
               c.caliber_group g, c.in_scope sc, c.in_main_stat m,
               (select count(*) from area_policy_map p where p.area_id=a.area_id
                 and p.rel in ('primary','support')) npol,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel='mention') nmen,
               (select s.publisher from area_source_map x join source s on s.source_id=x.source_id
                 where x.area_id=a.area_id limit 1) pub,
               (select s.credibility from area_source_map x join source s on s.source_id=x.source_id
                 where x.area_id=a.area_id order by case s.credibility when 'A' then 1 when 'B' then 2 else 3 end limit 1) cred,
               (select s.title from area_source_map x join source s on s.source_id=x.source_id
                 where x.area_id=a.area_id limit 1) src_title
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active' and a.founded_ymd is not null and a.founded_ymd <> ''
          and a.founded_ymd <= '2022-12-31'
        order by a.founded_ymd, a.area_id"""):
        r = dict(a)
        pro = regions.get(r["province_code"], {}).get("name", "")
        city = regions.get(r["city_code"], {}).get("name", "")
        cnty = regions.get(r["county_code"], {}).get("name", "")
        flags = []
        if not r["npol"]:
            flags.append("无硬依据")
        if r["status"] == "待核":
            flags.append("待核")
        if r["g"] == "D":
            flags.append("D组口径外")
        if r["founded_precision"] != "day":
            flags.append(f"时间精度={r['founded_precision']}")
        if r["nmen"] and not r["npol"]:
            flags.append("仅mention")
        r.update({"prov": pro, "city": city, "county": cnty, "flags": "；".join(flags)})
        rows.append(r)
    con.close()

    by_year = Counter((r["founded_ymd"] or "")[:4] for r in rows)
    n_flag = sum(1 for r in rows if r["flags"])
    print(f"2022 及以前成立：{len(rows)} 条｜带疑点 {n_flag} 条")
    for y, n in sorted(by_year.items()):
        print(f"  {y}: {n}")

    cols = ["area_id", "name", "prov", "city", "county", "founded_ymd", "founded_precision",
            "status", "type_code", "setup_kind", "g", "npol", "nmen", "cred", "pub",
            "flags", "cover_desc", "summary", "src_title"]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in cols} for r in rows])

    lines = ["# 2022 年及以前成立的片区清单", "",
             f"共 **{len(rows)}** 条，其中带疑点 **{n_flag}** 条。逐条明细见 `{OUT_CSV.name}`。", "",
             "## 按年份", "", "| 年 | 条数 |", "|---|---|"]
    for y, n in sorted(by_year.items()):
        lines.append(f"| {y} | {n} |")
    lines += ["", "## 疑点分布", ""]
    cnt = Counter()
    for r in rows:
        for fl in (r["flags"].split("；") if r["flags"] else []):
            cnt[fl.split("=")[0]] += 1
    lines += ["| 疑点 | 条数 |", "|---|---|"]
    for k, v in cnt.most_common():
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 逐条", "",
              "| area_id | 名称 | 省/市/县 | 成立 | 状态 | 口径 | 依据 | 疑点 |",
              "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['area_id']} | {r['name']} | {r['prov']}/{r['city']}/{r['county']} | "
                     f"{r['founded_ymd']} | {r['status']} | {CAL.get(r['g'], r['g'] or '')} | "
                     f"{r['npol']} | {r['flags']} |")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("->", OUT_MD.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
