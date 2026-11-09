"""一次性：检查 POL-SD10 与其它批次是否存在跨批次重复（purge 重灌前的前置核查）。"""
import glob
import json
import re

PAT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-]+")


def tk(title, county):
    return (PAT.sub("", title or ""), county or "")


sd10 = [
    json.loads(l)
    for l in open("data/stage/batches/POL-SD10-policy.jsonl", encoding="utf-8")
    if l.strip()
]
urls = {(r.get("url") or "").strip() for r in sd10}
docs = {
    ((r.get("doc_no") or "").strip(), (r.get("issuer") or "").strip())
    for r in sd10
    if (r.get("doc_no") or "").strip()
}
tks = {tk(r.get("title") or "", r.get("county_code") or "") for r in sd10}

hit = 0
for p in glob.glob("data/stage/batches/*.jsonl"):
    if "SD10" in p:
        continue
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        u = (r.get("url") or "").strip()
        d = ((r.get("doc_no") or "").strip(), (r.get("issuer") or "").strip())
        t = tk(r.get("title") or "", r.get("county_code") or "")
        if (u and u in urls) or (d[0] and d in docs) or (t[0] and t in tks):
            hit += 1
            print("重叠:", p.split("/")[-1].split("\\")[-1], r.get("title")[:50])

print(f"SD10 条数 {len(sd10)} / 跨批次重叠 {hit}")
