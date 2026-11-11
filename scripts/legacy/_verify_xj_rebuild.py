"""核对新疆 A650001–A650005 重建结果。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT area_id, name, town_codes, issuer, founded_ymd, founded_precision, "
    "cover_desc, summary, created_at, updated_at FROM area "
    "WHERE area_id LIKE 'A650%' ORDER BY area_id"
):
    print(f"{r['area_id']}  {r['name'][:28]}")
    print(f"   town_codes={r['town_codes']!r}  issuer={r['issuer']!r}")
    print(f"   founded={r['founded_ymd']!r}/{r['founded_precision']!r}")
    print(f"   cover_desc={r['cover_desc'][:46]!r}")
    print(f"   summary={r['summary'][:52]!r}…")
    print(f"   created_at={r['created_at']}  updated_at={r['updated_at']}")
    print()
