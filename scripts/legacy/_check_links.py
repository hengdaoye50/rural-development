import csv
from pathlib import Path

areas = list(csv.DictReader(Path("data/clean/area.csv").open(encoding="utf-8-sig", newline="")))
sources = {
    s["source_id"]: s
    for s in csv.DictReader(Path("data/clean/source.csv").open(encoding="utf-8-sig", newline=""))
}
mismatch = 0
for a in areas:
    sid = a.get("first_source_id")
    s = sources.get(sid)
    if not s:
        print("missing source row", a["area_id"], sid)
        continue
    if s["area_id"] != a["area_id"]:
        mismatch += 1
        if mismatch <= 10:
            print(f"area {a['area_id']} first={sid} source.area_id={s['area_id']} title={s['title'][:40]}")
print("mismatch", mismatch)
