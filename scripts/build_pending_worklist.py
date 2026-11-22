# -*- coding: utf-8 -*-
"""生成待核补采工单（按省分组，只读 + 落 CSV/MD）。

目标：把 566 条待核变成可派发的作业单——每条给出「缺什么、去哪儿找、找什么体裁」。

建议来源规则：
  - 省台账 `matched` 且有 policy → 「官方名单/方案原文（已有，核对是否点名）」
  - 省台账 `not_area`/`none` → 「市级名单、县级实施方案、乡镇级规划」
  - 仅 C 级来源 → 「补 A/B 级：省市县政府或部门公众号/网站原文」

用法：python scripts/build_pending_worklist.py
产出：data/stage/candidates/pending-worklist-{date}.csv
      reports/qa/待核工单-{date}.md
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
TODAY = date.today().isoformat()
CSV_OUT = ROOT / "data" / "stage" / "candidates" / f"pending-worklist-{TODAY}.csv"
MD_OUT = ROOT / "reports" / "qa" / f"待核工单-{TODAY}.md"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    roster = {r["province_code"]: dict(r) for r in con.execute(
        "select province_code, status, roster_name from province_roster")}
    pname = {r["region_code"]: r["name"] for r in con.execute("select region_code, name from region")}
    rows = []
    for a in con.execute("""
        select a.area_id, a.name, a.province_code, a.county_code, a.status, a.cover_desc,
               (select s.credibility from area_source_map m join source s on s.source_id=m.source_id
                 where m.area_id=a.area_id order by case s.credibility when 'A' then 1 when 'B' then 2
                 else 3 end limit 1) cred,
               (select s.publisher from area_source_map m join source s on s.source_id=m.source_id
                 where m.area_id=a.area_id limit 1) pub,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel='mention') nmen,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel in ('primary','support')) nh
        from area a where a.record_state='active' and a.status='待核'
        order by a.province_code, a.county_code, a.area_id"""):
        r = dict(a)
        rs = roster.get(r["province_code"], {})
        if r["nh"]:
            rec = "已有 primary/support，核对后可直接升级"
        elif rs.get("status") == "matched":
            rec = f"省名单已对账（{rs.get('roster_name') or ''}），找该名单逐条原文"
        elif rs.get("status") in ("not_area", "none"):
            rec = "省市县名单/实施方案（省级名单非片区，需市级或县级）"
        elif (r["cred"] or "C") <= "A":
            rec = "补原文：A/B 级已可用，核对正文是否点名"
        elif r["nmen"]:
            rec = "正文只提地名：找点名段或换文件"
        else:
            rec = "无政策挂接：先找设立文件"
        r["建议"] = rec
        r["省"] = pname.get(r["province_code"], r["province_code"])
        rows.append(r)
    con.close()

    print(f"待核 {len(rows)} 条")
    cnt = Counter(r["省"] for r in rows)
    for k, v in cnt.most_common(10):
        print(f"  {k}: {v}")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["area_id", "name", "省", "province_code", "county_code", "status",
            "cred", "pub", "nmen", "nh", "建议", "cover_desc"]
    tmp = CSV_OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    tmp.replace(CSV_OUT)

    lines = [f"# 待核补采工单（{TODAY}）", "",
             f"共 **{len(rows)}** 条待核，按省分布如下。逐条清单见 `{CSV_OUT.relative_to(ROOT).as_posix()}`。", "",
             "| 省 | 待核 | 建议优先找 |", "|---|---|---|"]
    for k, v in cnt.most_common():
        lines.append(f"| {k} | {v} | {roster.get(next((r['province_code'] for r in rows if r['省'] == k), ''), {}).get('status', '')} |")
    lines += ["", "## 前 40 条明细", "",
              "| area_id | 名称 | 省 | 县码 | 来源等级 | 建议 |", "|---|---|---|---|---|---|"]
    for r in rows[:40]:
        lines.append(f"| {r['area_id']} | {r['name'][:28]} | {r['省']} | {r['county_code']} | "
                     f"{r['cred'] or '-'} | {r['建议'][:40]} |")
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"工单 -> {CSV_OUT.relative_to(ROOT)}")
    print(f"摘要 -> {MD_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
