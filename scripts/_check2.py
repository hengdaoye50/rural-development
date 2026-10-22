import csv
from pathlib import Path

STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
for p in sorted(Path("data/clean/by_province").glob("*-area.csv")):
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
    print("====", p.name, len(rows))
    bad = 0
    for r in rows:
        problems = []
        if (r.get("status") or "") not in STATUS:
            problems.append("status=" + str(r.get("status")))
        if not (r.get("province_code") or "").isdigit():
            problems.append("prov=" + str(r.get("province_code")))
        if (r.get("founded_precision") or "") not in ("day", "month", "year", "unknown"):
            problems.append("prec=" + str(r.get("founded_precision")))
        if (r.get("record_state") or "") not in ("active", "superseded", "withdrawn"):
            problems.append("state=" + str(r.get("record_state")))
        if not r.get("cover_desc"):
            problems.append("no cover")
        if not r.get("county_code"):
            problems.append("no county")
        if problems:
            bad += 1
            if bad <= 8:
                print(" ", r.get("area_id"), r.get("name"), problems)
    print("bad", bad)

# sample new JS rows
rows = list(csv.DictReader(Path("data/clean/by_province/JS-area.csv").open(encoding="utf-8-sig", newline="")))
for r in rows:
    if r.get("area_id") in ("A320051", "A320053", "A320055", "A320058"):
        print("----", r["area_id"])
        for k, v in r.items():
            print(f"  {k}={v!r}")
