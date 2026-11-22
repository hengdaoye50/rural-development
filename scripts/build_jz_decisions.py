# -*- coding: utf-8 -*-
"""生成「集中推进区」清理裁定表（2026-11-22 第二批）。"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stage" / "candidates" / "clean-decisions-2026-11-22b.csv"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{ROOT/'data/db/片区库.sqlite3'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = []
    for r in con.execute("""select area_id,name,county_code from area
                            where record_state='active' and name like '%集中推进区%'
                            order by area_id"""):
        rows.append({"area_id": r["area_id"], "name": r["name"], "county_code": r["county_code"],
                     "建议": "drop",
                     "理由": "「衔接乡村振兴集中推进区」不是片区（docs/01 对象类型）"})
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
