"""查湖北 20 条样板带是否已在 belt 表，以及河南名单的实际可对账程度。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

print("=== 湖北 belt 现有 ===")
rows = conn.execute(
    "SELECT belt_id, name, county_code FROM belt WHERE province_code='420000' AND record_state='active'"
).fetchall()
print(f"{len(rows)} 条")
for r in rows:
    print(f"  {r['belt_id']} {r['name'][:34]}  {r['county_code']}")

print("\n=== 全国 belt 分布（前 10 省）===")
for r in conn.execute(
    "SELECT province_code p, COUNT(*) n FROM belt WHERE record_state='active' "
    "GROUP BY p ORDER BY n DESC LIMIT 10"
):
    print(f"  {r['p']} {r['n']}")

print("\n=== belt 表结构 ===")
print([x[1] for x in conn.execute("PRAGMA table_info(belt)")])
