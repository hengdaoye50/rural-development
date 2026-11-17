import csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig")))
bad = [r for r in rows if "repair-2026-09" in r["town_codes"] or "repair-2026-09" in r["scale_villages"]
       or "Northwest-batch01" in r["tags"]]
print(len(bad))
from collections import Counter
print(Counter((r["created_by"], r["province_code"]) for r in bad))
for r in bad[:6]:
    print(r["area_id"], "| created_by:", r["created_by"], "| tags parts:",
          len(r["tags"].split(",")), "| tail:", r["tags"].split(",")[-1][:24])
