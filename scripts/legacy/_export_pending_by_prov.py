"""把待核片区按省导出为 CSV，供定向查找的代理读取。"""
import csv
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row
OUT = ROOT / "data" / "stage" / "candidates"

PROV_ABBR = {
    "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
    "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
    "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
    "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
    "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
    "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
    "650000": "XJ",
}

rows = conn.execute("""
    SELECT a.area_id, a.name, a.province_code, a.county_code, s.url, s.publisher
    FROM area a LEFT JOIN source s ON s.source_id = a.first_source_id
    WHERE a.record_state='active' AND a.status='待核'
    ORDER BY a.province_code, a.area_id
""").fetchall()

by_prov = defaultdict(list)
for r in rows:
    by_prov[PROV_ABBR.get(r["province_code"], r["province_code"])].append(r)

OUT.mkdir(parents=True, exist_ok=True)
for abbr, items in sorted(by_prov.items()):
    p = OUT / f"pending-areas-{abbr}.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["area_id", "county_code", "name", "current_source_url", "current_publisher"])
        for r in items:
            w.writerow([r["area_id"], r["county_code"], r["name"],
                        r["url"] or "", r["publisher"] or ""])
    print(f"  {abbr} {len(items):>3} 条 -> {p.relative_to(ROOT)}")
