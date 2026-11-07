import json, re, csv
from pathlib import Path

ROOT = Path(r"D:\CODEX\全国乡村片区化数据库")
OUT = ROOT / "data" / "stage" / "POL-SH01-policy.jsonl"
raw = OUT.read_bytes()
print("bom=", raw[:3] == b"\xef\xbb\xbf", "bytes=", len(raw))

recs = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
print("records=", len(recs))

ids = set()
name = {}
with (ROOT / "data" / "stage" / "shards" / "SH01-counties.csv").open(encoding="utf-8-sig") as fh:
    for row in csv.DictReader(fh):
        for a in row["area_ids"].split("|"):
            ids.add(a)
            name[a] = (row["county_name"], row["area_names"])

linked = {}
for r in recs:
    for a in r["areas"]:
        linked.setdefault(a["area_id"], []).append(r["doc_no"] or r["title"][:12])
print("distinct areas linked=", len(linked))
for a in sorted(linked):
    print("  ", a, name.get(a, ("?", ""))[0], "<=", ",".join(linked[a]))

cov = {}
for r in recs:
    key = r["county_code"] or "310000(市级)"
    cov.setdefault(key, []).append(r["doc_no"] or "(无文号)")
print("coverage by county_code:")
for k in sorted(cov):
    print("  ", k, len(cov[k]), cov[k])

# spot checks
checks = {
    1: ["中期评估不合格的", "2025年2月11日", "沪委农办〔2025〕2号"],
    2: ["中期评估不合格的", "2024年4月4日", "沪乡村振兴办〔2024〕6号"],
    4: ["预拨付区级补助资金", "求好不求快", "沪奉农委〔2025〕59号"],
}
for i, needles in checks.items():
    t = recs[i - 1]["full_text"]
    print(f"rec{i:02d}", {n: (n in t) for n in needles})
print("slug dup=", len({r["slug"] for r in recs}) != len(recs))
print("has policy_id=", any("policy_id" in r for r in recs))
