"""核查是否存在「江西乐平（360281）」与「贵州黎平 lp.gov.cn」混淆的误录。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

print("=== URL 含 lp.gov.cn 的政策 ===")
for r in conn.execute(
    "SELECT policy_id, province_code, county_code, title, url FROM policy WHERE url LIKE '%lp.gov.cn%'"
):
    print(f"  {r['policy_id']} 省{r['province_code']} 县{r['county_code']} {r['title'][:44]}")
    print(f"      {r['url'][:90]}")

print("\n=== 360281 乐平市 的政策 ===")
for r in conn.execute(
    "SELECT policy_id, title, url FROM policy WHERE county_code='360281'"
):
    print(f"  {r['policy_id']} {r['title'][:44]}  {r['url'][:70]}")

print("\n=== 522631 黎平县（贵州）的政策 ===")
for r in conn.execute(
    "SELECT policy_id, title, url FROM policy WHERE county_code='522631'"
):
    print(f"  {r['policy_id']} {r['title'][:44]}  {r['url'][:70]}")

print("\n=== 江西首批批次的 province/county 分布核对 ===")
for r in conn.execute(
    "SELECT county_code, COUNT(*) n FROM policy "
    "WHERE created_by LIKE 'POL-JX-PILOT%' GROUP BY county_code ORDER BY county_code"
):
    print(f"  {r['county_code']} {r['n']}")
