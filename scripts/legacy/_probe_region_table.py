"""查看 region 表对辽宁的覆盖情况，确认县码来源是否够用。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT region_code, name, level FROM region WHERE region_code LIKE '21%' ORDER BY region_code"
).fetchall()
print(f"辽宁 region 行数 {len(rows)}")
for r in rows[:30]:
    print(f"  {r['region_code']} {r['name']} [{r['level']}]")

print("\n全表 level 分布：")
for r in conn.execute("SELECT level, COUNT(*) n FROM region GROUP BY level"):
    print(f"  {r['level']} {r['n']}")
