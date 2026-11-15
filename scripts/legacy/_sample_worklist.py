"""抽查补链清单里的 B2 / C 类，确认诊断。"""
import csv
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "reports/qa/link-repair-worklist.csv", encoding="utf-8-sig")))

b2 = [r for r in rows if r["grade"] == "B2"]
cc = [r for r in rows if r["grade"] == "C"]
print(f"B2 {len(b2)} 条，按省：{dict(collections.Counter(r['province_code'][:2] for r in b2).most_common(6))}\n")
for r in b2[:10]:
    print(f"  {r['area_id']} {r['name'][:24]:<26} 县{r['county_code']} 本县政策 {r['n_policy_in_county']} 份")

print(f"\nC 类 {len(cc)} 条，样例：")
for r in cc[:10]:
    print(f"  {r['area_id']} {r['name'][:24]:<26} 县{r['county_code']} 省{r['province_code']}")
