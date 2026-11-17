import csv, io, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

area = {r["area_id"]: r for r in csv.DictReader(io.open("data/clean/area.csv", encoding="utf-8-sig"))}
src = {r["source_id"]: r for r in csv.DictReader(io.open("data/clean/source.csv", encoding="utf-8-sig"))}
print("source cols:", list(next(iter(src.values())).keys()) if src else "EMPTY")

pend = [r for r in area.values() if r["status"] == "待核"]
print("待核", len(pend))

# 每个待核片区的 first_source 域
dom = collections.Counter()
detail = collections.defaultdict(list)
for r in pend:
    sid = r.get("first_source_id")
    s = src.get(sid)
    url = (s or {}).get("url", "")
    d = ""
    if url:
        d = url.split("/")[2] if "://" in url else url
    dom[d] += 1
    detail[d].append((r["area_id"], r["name"][:28], url))
print("\n== 待核唯一来源域名分布 ==")
for d, n in dom.most_common(20):
    print(f"{n:4d}  {d}")
