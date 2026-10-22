import csv
from pathlib import Path

ROOT = Path(".")
CLEAN = Path("data/clean")

# show bad belts
belts = list(csv.DictReader((CLEAN / "belt.csv").open(encoding="utf-8-sig", newline="")))
for b in belts:
    sid = b.get("source_id") or ""
    if not sid.startswith("S") or len(sid) > 12:
        print("BAD BELT", b.get("belt_id"), b.get("name"), "source_id=", repr(sid), "state=", b.get("record_state"), "prec=", b.get("year_precision"))

# orphans
areas = list(csv.DictReader((CLEAN / "area.csv").open(encoding="utf-8-sig", newline="")))
sources = list(csv.DictReader((CLEAN / "source.csv").open(encoding="utf-8-sig", newline="")))
sids = {s["source_id"] for s in sources}
srefs = {s["area_id"] for s in sources}
for a in areas:
    if a["area_id"] not in srefs and not a.get("first_source_id"):
        print("ORPHAN", a["area_id"], a.get("name"), a.get("status"))

# map FK
amap = list(csv.DictReader((CLEAN / "area_source_map.csv").open(encoding="utf-8-sig", newline="")))
for m in amap:
    if m.get("source_id") not in sids:
        print("MAP FK", m)
