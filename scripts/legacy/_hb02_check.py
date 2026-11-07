# -*- coding: utf-8 -*-
"""HB02 批次自检：字段完整性、.gov.cn 域名、area_id 合法、字数、重复。"""
import json, re, csv

VALID_AREAS = set()
for r in csv.DictReader(open("data/stage/shards/HB02-counties.csv", encoding="utf-8-sig")):
    VALID_AREAS.update(x for x in (r["area_ids"] or "").split(";") if x)

rows = [json.loads(l) for l in open("data/stage/batches/POL-HB02-policy.jsonl", encoding="utf-8") if l.strip()]
print("records:", len(rows))
errs = []
urls, docs = {}, {}
for i, r in enumerate(rows, 1):
    t = r["title"][:34]
    for k in r:
        pass
    if not r["full_text"].strip():
        errs.append((i, t, "empty full_text"))
    if not r["url"].startswith("http"):
        errs.append((i, t, "bad url"))
    host = re.sub(r"^https?://", "", r["url"]).split("/")[0]
    if not host.endswith(".gov.cn"):
        errs.append((i, t, "NON-GOV HOST " + host))
    if r["url"] in urls:
        errs.append((i, t, "dup url with #%d" % urls[r["url"]]))
    urls[r["url"]] = i
    if r["doc_no"]:
        key = (r["doc_no"], r["issuer"])
        if key in docs:
            errs.append((i, t, "dup doc_no"))
        docs[key] = i
    for a in r["areas"]:
        if a["area_id"] not in VALID_AREAS:
            errs.append((i, t, "bad area_id " + a["area_id"]))
        if a["entity_type"] != "area" or a["rel"] not in ("primary", "support", "mention"):
            errs.append((i, t, "bad area payload"))
    for e in r["events"]:
        if e["area_id"] not in VALID_AREAS:
            errs.append((i, t, "bad event area " + e["area_id"]))
    if r["issuer_level"] == "county" and not r["county_code"]:
        errs.append((i, t, "county level without county_code"))
    if r["issuer_level"] not in ("province", "city", "county", "town", "other"):
        errs.append((i, t, "bad issuer_level"))
    if r["source_kind"] not in ("政策文件", "政府公报", "部门动态", "新闻发布"):
        errs.append((i, t, "bad source_kind"))
    if r["credibility"] not in ("A", "B"):
        errs.append((i, t, "bad credibility"))
    if r["doc_type"] not in ("意见", "方案", "规划", "通知", "办法", "批复", "决定", "导则", "名单",
                             "公告", "动态", "答复", "指南", "总结", "报告", "其他"):
        errs.append((i, t, "bad doc_type " + r["doc_type"]))
    for f in ("budget_wan", "target_areas"):
        v = r[f]
        if v not in ("", None) and not re.fullmatch(r"\d+(\.\d+)?", str(v)):
            errs.append((i, t, "non numeric " + f + "=" + str(v)))
    if r["full_text_chars"] < 150 and r["source_kind"] == "政策文件":
        errs.append((i, t, "WARN short policy text %d" % r["full_text_chars"]))

print("errors:", len(errs))
for e in errs:
    print("  #%d %s -> %s" % e)

print("\n--- 分县统计 ---")
cc = {}
for r in rows:
    cc[r["county_code"] or "省级"] = cc.get(r["county_code"] or "省级", 0) + 1
for k, v in sorted(cc.items()):
    print("  %s: %d" % (k, v))
print("total chars:", sum(r["full_text_chars"] for r in rows))
