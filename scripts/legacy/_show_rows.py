import csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig")))
cols = list(rows[0].keys())
for aid in ("A630003", "A640005"):
    r = next(x for x in rows if x["area_id"] == aid)
    print("=" * 20, aid)
    for c in cols:
        print(f"  {c:20s} = {r[c][:70]!r}")
