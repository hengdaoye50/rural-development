import csv, io, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(io.open("reports/qa/misaligned-rows.csv", encoding="utf-8-sig")))
print("行数", len(rows))
for r in rows[:5] + rows[-3:]:
    print("\n===", r["area_id"], r["name"][:22])
    print("  tags          :", r["tags_before"][:50], "->", r["tags_after"][:30])
    print("  town_codes    :", r["town_codes_before"][:20], "->", r["town_codes_after"][:20])
    print("  cover_desc    :", r["cover_desc_before"][:20], "->", r["cover_desc_after"][:20])
    print("  scale_villages:", r["scale_villages_before"][:16], "->", r["scale_villages_after"][:16])
    print("  founded_ymd   :", r["founded_ymd_before"], "->", repr(r["founded_ymd_after"]))
    print("  summary_before:", r["summary_before"][:40])
    print("  summary_after :", r["summary_after"][:90])
