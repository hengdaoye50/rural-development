"""导出 C 类（本县无任何政策全文）空心片区清单，按省汇总供定向采集派发。"""
import csv
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "reports/qa/link-repair-worklist.csv", encoding="utf-8-sig")))
cc = [r for r in rows if r["grade"] == "C"]

by_prov = collections.defaultdict(list)
for r in cc:
    by_prov[r["province_code"]].append(r)

for prov, items in sorted(by_prov.items(), key=lambda x: -len(x[1])):
    print(f"=== {prov} ({len(items)}) ===")
    for r in items:
        print(f"  {r['area_id']} | {r['county_code']} | {r['name']}")
    print()
