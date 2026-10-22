"""Spot-check known date rows after quality pass."""
import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")

checks = {
    "YN": ["A530007", "A530001", "A530004"],
    "JS": ["A320001", "A320025"],
    "XZ": ["A540001", "A540003"],
    "ZJ": ["A330081", "A330089", "A330091"],
    "SD": ["A370001", "A370004"],
}

for prov, ids in checks.items():
    p = BY / f"{prov}-area.csv"
    rows = {r["area_id"]: r for r in csv.DictReader(p.open(encoding="utf-8-sig", newline=""))}
    for i in ids:
        r = rows.get(i)
        if not r:
            print(prov, i, "MISSING")
            continue
        print(
            f"{i} ymd={r.get('founded_ymd')!r} prec={r.get('founded_precision')!r} "
            f"lead={(r.get('lead_org') or '')[:24]!r} iss={(r.get('issuer') or '')[:24]!r} "
            f"cb={r.get('created_by')!r}"
        )
