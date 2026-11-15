"""列出 A 类与 B1 类的具体条目与命中政策，供人工确认后补挂。"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "reports/qa/link-repair-worklist.csv", encoding="utf-8-sig")))

for grade, label in (("A", "漏挂型"), ("B1", "形近型")):
    items = [r for r in rows if r["grade"] == grade]
    print(f"=== {grade} {label}（{len(items)}）===")
    for r in items:
        print(f"  {r['area_id']} | 县{r['county_code']} | {r['name']}")
        print(f"      命中政策 {r['hit_policy']}  形近名「{r['fuzzy_name']}」 {r['fuzzy_ratio']}")
    print()
