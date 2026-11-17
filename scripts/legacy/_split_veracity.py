import csv, io, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

rows = list(csv.DictReader(io.open("reports/qa/link-veracity.csv", encoding="utf-8-sig")))
hdr = list(rows[0].keys())

def dump(path, sel):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        w.writerows(sel)
    print(f"{path}: {len(sel)}")

dump("reports/qa/link-wrong.csv", [r for r in rows if r["tier"] in ("missing", "no_text")])
dump("reports/qa/link-weak.csv", [r for r in rows if r["tier"] == "place_only"])

# 省级点名率表（全量，写进报告用）
byarea = {}
for r in rows:
    k = r["area_id"]
    byarea.setdefault(k, {"name": r["area_name"], "prov": r["province_code"][:2], "tiers": []})
    byarea[k]["tiers"].append(r["tier"])
RANK = {"exact": 6, "core": 5, "stripped": 4, "tail": 3, "segments": 2, "place_only": 1, "missing": 0, "no_text": -1}
prov = defaultdict(lambda: {"n": 0, "named": 0, "weak": 0, "wrong": 0})
for k, v in byarea.items():
    best = max(v["tiers"], key=lambda t: RANK[t])
    p = prov[v["prov"]]
    p["n"] += 1
    if RANK[best] >= 2:
        p["named"] += 1
    elif best == "place_only":
        p["weak"] += 1
    else:
        p["wrong"] += 1
print("\n省 | 片区 | 点名 | 弱 | 无关 | 点名率")
for pc, d in sorted(prov.items(), key=lambda kv: kv[1]["named"] / kv[1]["n"]):
    print(f"{pc} | {d['n']} | {d['named']} | {d['weak']} | {d['wrong']} | {d['named']/d['n']*100:.0f}%")
