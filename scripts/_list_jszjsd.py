"""List JS/ZJ/SD area names already in by_province."""
import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
for prov, label in [("JS", "江苏"), ("ZJ", "浙江"), ("SD", "山东")]:
    rows = list(csv.DictReader((BY / f"{prov}-area.csv").open(encoding="utf-8-sig", newline="")))
    print(f"\n=== {label} {len(rows)} ===")
    for r in rows:
        print(f"{r['area_id']}\t{r['name']}\t{r['type_code']}\t{r['county_code']}\t{r['status']}")
