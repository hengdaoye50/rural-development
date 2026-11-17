import csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig")))
bad = [r for r in rows if "repair-2026-09" in r["town_codes"] or "repair-2026-09" in r["scale_villages"]
       or "Northwest-batch01" in r["tags"]]
for r in bad:
    parts = r["tags"].split(",")
    print(f"\n{r['area_id']} {r['name'][:24]}  parts={len(parts)}")
    for i, p in enumerate(parts):
        print(f"   [{i}] {p[:60]!r}")
