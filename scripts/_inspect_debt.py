"""Inspect problem rows for time/待核 reclassification."""
import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")

def dump(prov, ids):
    p = BY / f"{prov}-area.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
    for r in rows:
        if r.get("area_id") in ids:
            print("----", r.get("area_id"))
            for k in [
                "name", "type_code", "founded_ymd", "founded_precision", "status",
                "type_primary_note", "cover_desc", "summary", "first_source_id",
            ]:
                print(f"  {k}: {(r.get(k) or '')[:120]}")

print("=== LN A210005 ===")
dump("LN", {"A210005", "A210010"})
print("\n=== JL 五带 ===")
dump("JL", {"A220001", "A220002", "A220003", "A220004", "A220005"})
print("\n=== JL all 待核 / belt-like ===")
rows = list(csv.DictReader((BY / "JL-area.csv").open(encoding="utf-8-sig", newline="")))
for r in rows:
    if r.get("status") == "待核" or "带" in (r.get("name") or ""):
        print(r.get("area_id"), r.get("name"), r.get("type_code"), r.get("status"), r.get("founded_ymd"), r.get("founded_precision"))

print("\n=== ZJ 待核 sample ===")
rows = list(csv.DictReader((BY / "ZJ-area.csv").open(encoding="utf-8-sig", newline="")))
for r in rows:
    if r.get("status") == "待核":
        print(r.get("area_id"), r.get("name"), r.get("type_code"), r.get("founded_ymd"), r.get("founded_precision"), (r.get("type_primary_note") or "")[:60])

print("\n=== SD unknown time sample ===")
rows = list(csv.DictReader((BY / "SD-area.csv").open(encoding="utf-8-sig", newline="")))
for r in rows:
    if r.get("founded_precision") in ("", "unknown"):
        print(r.get("area_id"), r.get("name"), r.get("founded_ymd"), (r.get("summary") or "")[:70])
        if r.get("area_id") > "A370015":
            break
