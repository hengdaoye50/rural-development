"""Compare master vs by_province for area; report orphans."""
import csv
from pathlib import Path

CLEAN = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean")
BY = CLEAN / "by_province"

def ids(path, key):
    if not path.exists():
        return set()
    return {r.get(key) for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")) if r.get(key)}

master = ids(CLEAN / "area.csv", "area_id")
union = set()
for p in BY.glob("*-area.csv"):
    union |= ids(p, "area_id")
print("master", len(master), "by_province union", len(union))
print("only master", sorted(master - union)[:30], "count", len(master - union))
print("only by", sorted(union - master)[:10], "count", len(union - master))

mb = ids(CLEAN / "belt.csv", "belt_id")
ub = set()
for p in BY.glob("*-belt.csv"):
    ub |= ids(p, "belt_id")
print("belt master", len(mb), "by", len(ub))
print("belt only master", sorted(mb - ub)[:20], "count", len(mb - ub))
