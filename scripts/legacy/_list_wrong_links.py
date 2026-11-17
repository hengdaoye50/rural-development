import csv, io, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("reports/qa/link-veracity.csv", encoding="utf-8-sig")))
bad = [r for r in rows if r["tier"] == "missing"]
print("完全无关链接", len(bad))
byarea = defaultdict(list)
for r in rows:
    byarea[(r["area_id"], r["area_name"], r["province_code"])].append(r)
for r in bad:
    print(f"{r['area_id']} {r['province_code'][:2]} 「{r['area_name']}」 {r['rel']} {r['policy_id']}")
    print(f"      {r['policy_title']}")
print("\n== 全部依据都是无关链接的片区（需处置）==")
orphan = [(k, v) for k, v in byarea.items() if all(x["tier"] == "missing" for x in v)]
for (aid, aname, pc), v in orphan:
    print(f"  {aid} {pc[:2]} 「{aname}」 status={v[0]['area_status']} 链接{len(v)}")
