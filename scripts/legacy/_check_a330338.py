"""自查：A330338 的名称到底是什么，之前挂 P330005（诗画琏溪）是否挂错。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for aid in ("A330337", "A330338", "A330341"):
    r = conn.execute(
        "SELECT area_id, name, name_norm, county_code, cover_desc, summary FROM area WHERE area_id=?",
        (aid,),
    ).fetchone()
    print(dict(r) if r else f"{aid} 不存在")
    print()

print("=== A330338 的现有挂接 ===")
for r in conn.execute(
    "SELECT m.policy_id, m.rel, p.title FROM area_policy_map m "
    "JOIN policy p ON p.policy_id=m.policy_id WHERE m.area_id='A330338'"
):
    print(f"  {r['policy_id']} {r['rel']}  {r['title'][:60]}")
