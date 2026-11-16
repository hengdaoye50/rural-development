"""江西全省试点准备：县清单、现有片区与政策、已有政府工作报告覆盖情况。"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

counties = []
with (ROOT / "data" / "clean" / "region.csv").open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["level"] == "county" and r["region_code"].startswith("36"):
            counties.append((r["region_code"], r["name"], r["parent_code"]))

print(f"江西县级单元 {len(counties)} 个")

have_area = {r["county_code"] for r in conn.execute(
    "SELECT DISTINCT county_code FROM area WHERE province_code='360000' AND record_state='active'")}
have_report = {r["county_code"] for r in conn.execute(
    "SELECT DISTINCT county_code FROM policy WHERE province_code='360000' "
    "AND doc_type='报告' AND title LIKE '%政府工作报告%' AND county_code != ''")}

print(f"库内有片区的县 {len(have_area)}；已有政府工作报告的县 {len(have_report)}")

# 按市分组输出，便于分批派发
by_city: dict[str, list] = {}
for code, name, parent in counties:
    by_city.setdefault(parent, []).append((code, name, code in have_area, code in have_report))

city_name = {r["region_code"]: r["name"] for r in conn.execute(
    "SELECT region_code, name FROM region WHERE level='city'")}

total = 0
for parent, items in sorted(by_city.items()):
    print(f"\n{city_name.get(parent, parent)}（{len(items)} 县）")
    for code, name, ha, hr in items:
        flag = ("片区" if ha else "  -") + ("/有报告" if hr else "")
        print(f"  {code} {name:<10} {flag}")
        total += 1
print(f"\n合计 {total}")
