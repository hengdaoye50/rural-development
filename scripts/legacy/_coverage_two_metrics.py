"""对比两种覆盖率口径：含 mention / 只算 primary+support。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")

total = conn.execute("SELECT COUNT(*) FROM area WHERE record_state='active'").fetchone()[0]
any_rel = conn.execute(
    "SELECT COUNT(DISTINCT area_id) FROM area_policy_map WHERE entity_type='area'"
).fetchone()[0]
strong = conn.execute(
    "SELECT COUNT(DISTINCT area_id) FROM area_policy_map "
    "WHERE entity_type='area' AND rel IN ('primary','support')"
).fetchone()[0]
only_mention = conn.execute(
    """
    SELECT COUNT(DISTINCT m.area_id) FROM area_policy_map m
    WHERE m.entity_type='area' AND m.rel='mention'
      AND NOT EXISTS (SELECT 1 FROM area_policy_map x
                      WHERE x.area_id=m.area_id AND x.rel IN ('primary','support'))
    """
).fetchone()[0]

print(f"片区总数（active）      {total}")
print(f"含 mention 口径        {any_rel}  ({any_rel/total*100:.1f}%)")
print(f"仅 primary+support     {strong}  ({strong/total*100:.1f}%)")
print(f"仅靠 mention 支撑的     {only_mention}  ← 这批严格说不算有政策依据")

print("\n按 rel 计数：")
for r in conn.execute(
    "SELECT rel, COUNT(*) n FROM area_policy_map WHERE entity_type='area' GROUP BY rel ORDER BY n DESC"
):
    print(f"  {r[0]:<8} {r[1]}")
