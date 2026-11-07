import json, sys, csv, collections
sys.stdout.reconfigure(encoding="utf-8")
P = r"D:\CODEX\全国乡村片区化数据库\data\stage\POL-ZJ03-policy.jsonl"
CSV = r"D:\CODEX\全国乡村片区化数据库\data\stage\shards\ZJ03-counties.csv"
VALID = []
with open(CSV, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        for a in row["area_ids"].split("|"):
            VALID.append((a.strip(), row["county_code"]))
valid_ids = {a for a, c in VALID}
rows = [json.loads(l) for l in open(P, encoding="utf-8")]
print("n =", len(rows))
print("非 .gov.cn:", [r["url"] for r in rows if ".gov.cn" not in r["url"]])
REQ = ("title", "doc_no", "issuer", "issuer_level", "issued_ymd", "published_ymd", "doc_type",
       "source_kind", "province_code", "city_code", "county_code", "instruments", "scope_desc",
       "target_areas", "budget_wan", "valid_state", "url", "credibility", "summary", "slug",
       "fetched_at", "full_text", "areas", "events")
bad = [(r["title"][:20], k) for r in rows for k in REQ if k not in r]
print("字段缺失:", bad)
print("credibility:", dict(collections.Counter(r["credibility"] for r in rows)))
print("issuer_level:", dict(collections.Counter(r["issuer_level"] for r in rows)))
print("source_kind:", dict(collections.Counter(r["source_kind"] for r in rows)))
print("doc_type:", dict(collections.Counter(r["doc_type"] for r in rows)))
print("county:", dict(collections.Counter(r["county_code"] or "(市级)" for r in rows)))
errs = 0
for r in rows:
    for a in r["areas"]:
        if a["area_id"] not in valid_ids:
            print("  BAD area_id", a["area_id"], "in", r["title"][:40]); errs += 1
        if (a["area_id"], a["rel"]) and a["rel"] not in ("primary", "support", "mention"):
            print("  BAD rel", a); errs += 1
        if r["county_code"] and (a["area_id"], r["county_code"]) not in VALID:
            print("  CROSS-COUNTY area", a["area_id"], "in", r["title"][:40]); errs += 1
    for e in r["events"]:
        if e["event_type"] not in ("设立", "挂牌", "批复", "入选", "扩围", "更名", "撤销"):
            print("  BAD event_type", e); errs += 1
        if e["area_id"] not in valid_ids:
            print("  BAD event area", e); errs += 1
print("area/event 错误数:", errs)
print("已挂接 area_id:", sorted({a["area_id"] for r in rows for a in r["areas"]}))
print("正文 min/max:", min(r["full_text_chars"] for r in rows), max(r["full_text_chars"] for r in rows))
print("target_areas 非空:", [(r["county_code"] or "市", r["target_areas"]) for r in rows if r["target_areas"] != ""])
print("budget_wan 非空:", [(r["county_code"] or "市", r["budget_wan"]) for r in rows if r["budget_wan"] != ""])
