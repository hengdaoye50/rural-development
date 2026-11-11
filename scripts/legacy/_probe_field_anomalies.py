"""排查两个会污染统计的字段异常：founded_ymd 非日期值、budget_wan 极值。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

print("=== founded_ymd 非日期值 ===")
bad = []
for r in conn.execute(
    "SELECT area_id, name, founded_ymd, founded_precision FROM area "
    "WHERE record_state='active' AND founded_ymd IS NOT NULL AND founded_ymd != ''"
):
    if not DATE.match(r["founded_ymd"].strip()):
        bad.append(dict(r))
print(f"共 {len(bad)} 条")
for b in bad:
    print(f"  {b['area_id']}  {b['founded_ymd']!r}  precision={b['founded_precision']!r}  {b['name'][:26]}")

print("\n=== budget_wan 最大的 6 条 ===")
for r in conn.execute(
    "SELECT policy_id, title, budget_wan, province_code FROM policy "
    "WHERE budget_wan IS NOT NULL AND budget_wan != '' "
    "ORDER BY CAST(budget_wan AS REAL) DESC LIMIT 6"
):
    print(f"  {r['policy_id']} [{r['province_code']}] {r['budget_wan']} 万元  {r['title'][:52]}")

print("\n=== budget_wan 最小的 4 条 ===")
for r in conn.execute(
    "SELECT policy_id, title, budget_wan FROM policy "
    "WHERE budget_wan IS NOT NULL AND budget_wan != '' "
    "ORDER BY CAST(budget_wan AS REAL) ASC LIMIT 4"
):
    print(f"  {r['policy_id']} {r['budget_wan']} 万元  {r['title'][:52]}")
