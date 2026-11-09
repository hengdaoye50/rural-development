import csv
import io
import json
import os

BATCH = "data/stage/batches/POL-TJ01-policy.jsonl"
CANON = "data/stage/shards/TJ01-counties.csv"

with io.open(CANON, encoding="utf-8-sig") as fh:
    rows = list(csv.DictReader(fh))
allowed = set()
names = {}
for r in rows:
    for a in r["area_ids"].split("|"):
        allowed.add(a)
        names[a] = (r["county_code"], r["area_names"])

raw = io.open(BATCH, "rb").read()
print("bytes:", len(raw), "CRLF:", raw.count(b"\r\n"), "lines:", raw.count(b"\n"))
bad = 0
n_areas = {}
for i, line in enumerate(io.open(BATCH, encoding="utf-8"), 1):
    line = line.rstrip("\n")
    if not line:
        continue
    o = json.loads(line)
    assert "policy_id" not in o and "event_id" not in o, f"line {i} has id"
    assert "gov.cn" in o["url"], f"line {i} url"
    assert o["source_kind"] in ("政策文件", "政府公报", "部门动态", "新闻发布"), i
    assert o["credibility"] in ("A", "B"), i
    for a in o["areas"]:
        if a["area_id"] not in allowed:
            print(f"BAD area {a['area_id']} in line {i}")
            bad += 1
        n_areas[a["area_id"]] = n_areas.get(a["area_id"], 0) + 1
    for e in o["events"]:
        if e["area_id"] not in allowed:
            print(f"BAD event area {e['area_id']} line {i}")
            bad += 1
    if len(o["full_text"]) < 150:
        print("SHORT full_text line", i)
        bad += 1
print("bad:", bad)
print("coverage per area:")
for a in sorted(allowed):
    cc, nm = names[a]
    print(f"  {a} {cc} {nm}: records={n_areas.get(a,0)}")
print("total records:", sum(1 for _ in io.open(BATCH, encoding="utf-8")))
