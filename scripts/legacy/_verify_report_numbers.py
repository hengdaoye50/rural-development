"""核对研究报告里引用的几个数字。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

print("=== 强村公司 按省分布 ===")
for r in conn.execute(
    "SELECT province_code, COUNT(*) n FROM policy WHERE instruments LIKE '%强村公司%' "
    "GROUP BY province_code ORDER BY n DESC LIMIT 6"
):
    print(f"  {r['province_code']} {r['n']}")

print("\n=== 无政策依据片区数 ===")
tot = conn.execute("SELECT COUNT(*) FROM area WHERE record_state='active'").fetchone()[0]
cov = conn.execute(
    "SELECT COUNT(DISTINCT area_id) FROM area_policy_map WHERE entity_type='area'"
).fetchone()[0]
strong = conn.execute(
    "SELECT COUNT(DISTINCT area_id) FROM area_policy_map "
    "WHERE entity_type='area' AND rel IN ('primary','support')"
).fetchone()[0]
print(f"  片区 {tot} / 含mention {cov} / 严格 {strong} → 未覆盖 {tot-cov}")

print("\n=== 浙江 / 山东 当前空心 ===")
for prov, name in (("330000", "浙江"), ("370000", "山东")):
    a = conn.execute(
        "SELECT COUNT(*) FROM area WHERE province_code=? AND record_state='active'", (prov,)
    ).fetchone()[0]
    c = conn.execute(
        "SELECT COUNT(DISTINCT m.area_id) FROM area_policy_map m "
        "JOIN area a ON a.area_id=m.area_id "
        "WHERE a.province_code=? AND a.record_state='active'", (prov,)
    ).fetchone()[0]
    print(f"  {name} {c}/{a} 空心 {a-c}")

print("\n=== 成立年份（只统计合法日期）===")
import re
DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
years = {}
for r in conn.execute(
    "SELECT founded_ymd y FROM area WHERE record_state='active' "
    "AND founded_ymd IS NOT NULL AND founded_ymd != ''"
):
    v = r["y"].strip()
    if DATE.match(v):
        years[v[:4]] = years.get(v[:4], 0) + 1
for y in sorted(years):
    print(f"  {y} {years[y]}")
print("  合计", sum(years.values()))
