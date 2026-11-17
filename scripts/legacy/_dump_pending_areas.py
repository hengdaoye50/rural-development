"""导出待核片区清单（按省分组），供定向查找官方依据。"""
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT a.area_id, a.name, a.province_code, a.county_code, s.publisher
    FROM area a LEFT JOIN source s ON s.source_id = a.first_source_id
    WHERE a.record_state='active' AND a.status='待核'
    ORDER BY a.province_code, a.area_id
""").fetchall()

by_prov = defaultdict(list)
for r in rows:
    by_prov[r["province_code"]].append(r)

print(f"待核合计 {len(rows)} 条，{len(by_prov)} 个省\n")
for p, items in sorted(by_prov.items(), key=lambda x: -len(x[1])):
    print(f"=== {p}（{len(items)}）===")
    for r in items:
        print(f"  {r['area_id']} | {r['county_code']} | {r['name']} | 来源:{r['publisher'] or '-'}")
    print()
