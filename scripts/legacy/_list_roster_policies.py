"""列出本轮新入库的名单政策编号。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, province_code, target_areas, title FROM policy "
    "WHERE created_by LIKE '%ROSTER%' OR title LIKE '%先导区名单%' OR title LIKE '%百千万%' "
    "ORDER BY province_code, policy_id"
):
    print(f"{r['policy_id']} [{r['province_code']}] ta={r['target_areas'] or '-'} {r['title'][:52]}")
