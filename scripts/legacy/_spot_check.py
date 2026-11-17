import csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("reports/qa/misaligned-rows.csv", encoding="utf-8-sig")))
want = {"A610001", "A330083", "A330152", "A320003", "A210001"}
for r in rows:
    if r["area_id"] in want:
        print(f"\n=== {r['area_id']} {r['name'][:24]} [{r['kind']}]")
        for c in ("tags", "town_codes", "cover_desc", "scale_villages", "founded_ymd", "founded_precision", "summary"):
            b, a = r[f"{c}_before"], r[f"{c}_after"]
            mark = "  " if b == a else "->"
            print(f"  {c:17s} {b[:40]!r:44s}{mark} {a[:50]!r}")
print("\n按 kind 统计：")
from collections import Counter
print(Counter(r["kind"] for r in rows))
