"""江西各市县级单元数，用于分批派发。"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
city = {r[0]: r[1] for r in conn.execute("SELECT region_code, name FROM region WHERE level='city'")}

d: dict[str, list[str]] = {}
with (ROOT / "data" / "clean" / "region.csv").open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["level"] == "county" and r["region_code"].startswith("36"):
            d.setdefault(r["parent_code"], []).append(r["name"])

for k, v in sorted(d.items(), key=lambda x: -len(x[1])):
    print(f"{k} {city.get(k, '?'):<8} {len(v):>3}  {'、'.join(v)}")
print("total", sum(len(v) for v in d.values()))
