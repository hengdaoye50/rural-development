"""一次性：定位需要补映射的 policy_id。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
c.row_factory = sqlite3.Row

print("--- 辽宁 2023 名单 ---")
for r in c.execute(
    "SELECT policy_id, title, local_path FROM policy "
    "WHERE province_code = '210000' AND (title LIKE '%示范带%' OR title LIKE '%名单%')"
):
    print(r["policy_id"], r["title"][:70])

print("--- 天津 市级实施方案 ---")
for r in c.execute(
    "SELECT policy_id, title FROM policy WHERE policy_id = 'P120001'"
):
    print(r["policy_id"], r["title"][:70])

print("--- 目标片区名 ---")
for r in c.execute(
    "SELECT area_id, name, county_code FROM area WHERE area_id IN ('A120007','A210009')"
):
    print(dict(r))
