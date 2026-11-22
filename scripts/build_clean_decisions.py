# -*- coding: utf-8 -*-
"""生成 2026-11-22 口径清理裁定表（贵州组片区 / 安州规划分区 / 泰安示范区）。"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stage" / "candidates" / "clean-decisions-2026-11-22.csv"

SEL = {
    "贵州组片区": ("520000", "name like '%组片区%' or name in ('上坝片区（金沙木孔）','焦家村、靛山村（普定集成试点）')",
              "对象是村民组/村，不是片区（docs/01 对象层级）"),
    "安州规划分区": ("510000", "area_id in ('A510002','A510003')",
                "疑为国土空间规划分区，非乡村振兴片区"),
    "泰安示范区": ("370000", "city_code='370900' and name like '%乡村振兴示范区%' and name not like '%示范片区%'",
              "对象是「乡村振兴示范区」，不是「片区」"),
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{ROOT/'data/db/片区库.sqlite3'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = []
    for tag, (prov, cond, why) in SEL.items():
        for r in con.execute(f"select area_id,name,county_code from area "
                             f"where province_code=? and record_state='active' and ({cond})", (prov,)):
            rows.append({"area_id": r["area_id"], "name": r["name"], "建议": "drop",
                         "理由": f"{tag}：{why}", "county_code": r["county_code"]})
    con.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["area_id", "name", "county_code", "建议", "理由"],
                           lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(OUT)
    print(f"{len(rows)} 条 -> {OUT.relative_to(ROOT)}")
    for r in rows:
        print(f"  {r['area_id']} {r['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
