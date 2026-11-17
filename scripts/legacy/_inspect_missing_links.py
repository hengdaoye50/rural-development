import csv, io, sys, sqlite3, re
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "."

rows = list(csv.DictReader(io.open("reports/qa/link-veracity.csv", encoding="utf-8-sig")))
miss = [r for r in rows if r["tier"] == "missing" and r["rel"] == "primary"]
print("missing+primary", len(miss))

# 抽 贵州/广东/辽宁 各几条
byprov = defaultdict(list)
for r in miss:
    byprov[r["province_code"][:2]].append(r)

for p in ["52", "44", "21", "33", "32", "37"]:
    print("\n===== 省", p, "missing primary", len(byprov[p]))
    for r in byprov[p][:4]:
        print(f"  {r['area_id']} 「{r['area_name']}」")
        print(f"     policy {r['policy_id']} {r['policy_title']}")
        print(f"     path {r['local_path']}")
