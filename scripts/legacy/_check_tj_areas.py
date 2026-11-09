"""一次性：查天津 A120006/A120007 的既有依据，供 TJ02 续采判断映射关系。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
c.row_factory = sqlite3.Row

for r in c.execute(
    "SELECT area_id, name, county_code, cover_desc FROM area WHERE area_id IN ('A120006','A120007')"
):
    print(dict(r))

print("--- 已挂政策 ---")
for r in c.execute(
    "SELECT m.area_id, m.rel, p.policy_id, p.title "
    "FROM area_policy_map m JOIN policy p ON p.policy_id = m.policy_id "
    "WHERE m.area_id IN ('A120006','A120007')"
):
    print(r["area_id"], r["rel"], r["policy_id"], r["title"][:60])
