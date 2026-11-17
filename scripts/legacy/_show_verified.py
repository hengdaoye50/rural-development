"""查看核验批次补上了哪些待核片区。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT m.area_id, m.rel, a.name, a.status, p.policy_id, p.title
    FROM area_policy_map m
    JOIN area a ON a.area_id = m.area_id
    JOIN policy p ON p.policy_id = m.policy_id
    WHERE p.created_by LIKE '%VERIFY%'
    ORDER BY m.area_id
""").fetchall()

print(f"核验批次写入的映射 {len(rows)} 条：")
for r in rows:
    print(f"  {r['area_id']} [{r['rel']}] {r['name'][:24]:<26} status={r['status']}")
    print(f"      ← {r['policy_id']} {r['title'][:44]}")
