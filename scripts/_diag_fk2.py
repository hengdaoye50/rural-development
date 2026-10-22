import csv
from pathlib import Path

CLEAN = Path("data/clean")
regions = {r["region_code"] for r in csv.DictReader((CLEAN / "region.csv").open(encoding="utf-8-sig", newline=""))}
sources = {s["source_id"] for s in csv.DictReader((CLEAN / "source.csv").open(encoding="utf-8-sig", newline=""))}
areas = {a["area_id"] for a in csv.DictReader((CLEAN / "area.csv").open(encoding="utf-8-sig", newline=""))}
belts = {b["belt_id"] for b in csv.DictReader((CLEAN / "belt.csv").open(encoding="utf-8-sig", newline=""))}

print("counts", len(areas), len(belts), len(sources), len(regions))

for r in csv.DictReader((CLEAN / "area_region_map.csv").open(encoding="utf-8-sig", newline="")):
    if r.get("region_code") not in regions:
        print("ARM region", r)
        break
else:
    print("area_region_map region ok")

for r in csv.DictReader((CLEAN / "belt_region_map.csv").open(encoding="utf-8-sig", newline="")):
    if r.get("region_code") not in regions:
        print("BRM region", r)
    if r.get("belt_id") not in belts:
        print("BRM belt", r)

for r in csv.DictReader((CLEAN / "area_source_map.csv").open(encoding="utf-8-sig", newline="")):
    if r.get("source_id") not in sources:
        print("ASM source", r)
        break
else:
    print("area_source_map source ok")

# belt source empty?
for b in csv.DictReader((CLEAN / "belt.csv").open(encoding="utf-8-sig", newline="")):
    if not b.get("source_id"):
        print("belt empty sid", b.get("belt_id"))

# AH areas status
for a in csv.DictReader((CLEAN / "area.csv").open(encoding="utf-8-sig", newline="")):
    if a["area_id"].startswith("A34001"):
        print(a["area_id"], a.get("status"), a.get("first_source_id"))
