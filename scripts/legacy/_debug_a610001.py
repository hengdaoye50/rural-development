import csv, io, re, sys
sys.stdout.reconfigure(encoding="utf-8")
DATEISH = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:+\-]+)?$")

rows = list(csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig")))
r = next(x for x in rows if x["area_id"] == "A610001")
print("A610001 修复后各字段：")
for k, v in r.items():
    print(f"  {k:18s} = {v[:70]!r}")

# 审计 CSV 里它的原始合并串
au = list(csv.DictReader(io.open("reports/qa/misaligned-rows.csv", encoding="utf-8-sig")))
a = next((x for x in au if x["area_id"] == "A610001"), None)
if a:
    print("\n原始 tags_before =", a["tags_before"][:160])
    print("parts =", [p[:30] for p in a["tags_before"].split(",")])

# 剩余 summary 为日期的行，按 created_by 分组
from collections import Counter
bad = [x for x in rows if DATEISH.match(x["summary"].strip())]
print(f"\nsummary 为日期: {len(bad)}")
print(Counter(x["created_by"] for x in bad))
print("\n浙江 tags 多段的行：")
for x in rows:
    if len(x["tags"].split(",")) >= 3:
        print(f"  {x['area_id']} created_by={x['created_by']:18s} tags={x['tags'][:70]!r}")
print("\ncover_desc 含批次名的行：")
for x in rows:
    if "batch" in x["cover_desc"] or "repair-" in x["cover_desc"]:
        print(f"  {x['area_id']} created_by={x['created_by']:18s} cover_desc={x['cover_desc'][:60]!r}")
