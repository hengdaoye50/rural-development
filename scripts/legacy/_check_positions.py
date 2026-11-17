import csv, io, re, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("reports/qa/misaligned-rows.csv", encoding="utf-8-sig")))
NUM = re.compile(r"^\d+(\.\d+)?$")
DATEISH = re.compile(r"^\d{4}-\d{2}-\d{2}")
ok2 = ok3 = 0
for r in rows:
    parts = r["tags_before"].split(",")
    p2 = parts[2] if len(parts) > 2 else "<缺>"
    p1 = parts[1] if len(parts) > 1 else "<缺>"
    nums = [p for p in parts[2:] if NUM.match(p.strip())]
    plausible2 = 2 <= len(p2) <= 60 and not NUM.match(p2) and not DATEISH.match(p2) and "repair" not in p2 and "batch" not in p2
    ok2 += plausible2
    ok3 += bool(nums)
    print(f"{r['area_id']} n={len(parts):2d} p1={p1[:14]:15s} p2ok={int(plausible2)} p2={p2[:34]:36s} nums={nums[:2]}")
print(f"\nparts[2] 像 cover_desc 的: {ok2}/{len(rows)}；能从 parts[2:] 找到数字 scale 的: {ok3}/{len(rows)}")
