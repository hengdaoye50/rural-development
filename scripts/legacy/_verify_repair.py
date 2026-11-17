import csv, io, re, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig")))
print("area 行数", len(rows))
BATCH = "repair-2026-09"
DATEISH = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:+\-]+)?$")
bad = {
    "town_codes含批次名": [r for r in rows if BATCH in r["town_codes"]],
    "cover_desc含批次名": [r for r in rows if BATCH in r["cover_desc"]],
    "summary为日期": [r for r in rows if DATEISH.match(r["summary"].strip())],
    "founded_ymd占位": [r for r in rows if r["founded_ymd"] == "2024-01-01"],
    "tags多段(被合并)": [r for r in rows if len(r["tags"].split(",")) >= 3 and r["created_by"] == BATCH],
}
for k, v in bad.items():
    print(f"{k}: {len(v)}")
    for r in v[:5]:
        print("   ", r["area_id"], r["name"][:22])
print("\n抽样检查修复后 5 行：")
for r in [x for x in rows if x["area_id"] in
          ("A320003", "A610001", "A620002", "A630003", "A640005")]:
    print(f"\n{r['area_id']} {r['name'][:24]}")
    print("   tags      :", r["tags"])
    print("   town_codes:", r["town_codes"])
    print("   cover_desc:", r["cover_desc"][:60])
    print("   scale_vill:", r["scale_villages"], "| founded:", repr(r["founded_ymd"]), r["founded_precision"])
    print("   summary   :", r["summary"][:80])
