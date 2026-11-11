"""核查 A370066（院东头镇片区）的县码：SD09 代理报称应属沂水县 371323 而非沂南县 371321。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

r = conn.execute(
    "SELECT area_id, name, county_code, city_code, town_codes, cover_desc, summary "
    "FROM area WHERE area_id = 'A370066'"
).fetchone()
print(dict(r) if r else "A370066 不存在")

print("\n=== 院东头 / 沂水 相关片区 ===")
for x in conn.execute(
    "SELECT area_id, name, county_code FROM area "
    "WHERE name LIKE '%院东头%' OR name LIKE '%沂水%' OR cover_desc LIKE '%院东头%'"
):
    print(f"  {x['area_id']} {x['name'][:32]}  county={x['county_code']}")

print("\n=== 沂水/沂南 各县码下的片区数 ===")
for x in conn.execute(
    "SELECT county_code, COUNT(*) n FROM area WHERE county_code IN ('371321','371323') "
    "AND record_state='active' GROUP BY county_code"
):
    print(f"  {x['county_code']}: {x['n']}")
