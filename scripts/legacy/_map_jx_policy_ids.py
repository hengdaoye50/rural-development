"""找出赣州试点批次的 policy_id，供建 area 时挂接来源。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, county_code, title, full_text_chars FROM policy "
    "WHERE province_code='360000' AND created_by LIKE 'POL-JX-PILOT%' "
    "ORDER BY county_code"
):
    print(f"{r['county_code']}  {r['policy_id']}  {r['full_text_chars']:>6}字  {r['title'][:40]}")
