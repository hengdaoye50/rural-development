import json
import re
from pathlib import Path
from urllib.parse import urlparse

P = Path("data/stage/batches/POL-GD02-policy.jsonl")
ALLOWED_AREAS = {"A440029", "A440028", "A440032", "A440031", "A440034",
                 "A440011", "A440012", "A440013", "A440014", "A440015",
                 "A440016", "A440036"}
VALID_KINDS = {"政策文件", "政府公报", "部门动态", "新闻发布"}
VALID_LEVELS = {"province", "city", "county", "town", "other"}
VALID_DOC_TYPES = {"意见", "方案", "规划", "通知", "办法", "批复", "决定", "导则",
                   "名单", "公告", "动态", "答复", "指南", "总结", "报告", "其他"}
COUNTY = {"440605", "440607", "440783", "440981", "441225", "441322", "441403", "441581"}

rows = []
bad = 0
for i, line in enumerate(P.read_text(encoding="utf-8").splitlines(), 1):
    o = json.loads(line)
    rows.append(o)
    host = urlparse(o["url"]).netloc
    problems = []
    if not host.endswith(".gov.cn"):
        problems.append("非gov.cn域名 " + host)
    if o["source_kind"] not in VALID_KINDS:
        problems.append("source_kind " + o["source_kind"])
    if o["credibility"] not in {"A", "B"}:
        problems.append("credibility " + o["credibility"])
    if o["issuer_level"] not in VALID_LEVELS:
        problems.append("issuer_level " + o["issuer_level"])
    if o["doc_type"] not in VALID_DOC_TYPES:
        problems.append("doc_type " + o["doc_type"])
    if o.get("county_code") and o["county_code"] not in COUNTY:
        problems.append("county_code " + o["county_code"])
    if o["issuer_level"] == "county" and not o.get("county_code"):
        problems.append("county 级缺 county_code")
    for a in o.get("areas") or []:
        if a["area_id"] not in ALLOWED_AREAS:
            problems.append("area_id " + a["area_id"])
        if a.get("rel") not in {"primary", "support", "mention"}:
            problems.append("rel " + str(a.get("rel")))
    if len(o["full_text"]) < 150:
        problems.append("full_text 过短 %d" % len(o["full_text"]))
    if not o.get("policy_id") and not o.get("event_id"):
        pass
    else:
        problems.append("不应带 policy_id/event_id")
    print("%2d %-6s %-9s %-5s %-6s chars=%-6d %s" % (
        i, o.get("county_code") or "-", o["source_kind"], o["credibility"],
        o["doc_type"], len(o["full_text"]), o["title"][:34]))
    if problems:
        bad += 1
        print("    !! " + " | ".join(problems))

print("\n共 %d 条；问题条数 %d" % (len(rows), bad))
kinds = {}
for o in rows:
    kinds[o["source_kind"]] = kinds.get(o["source_kind"], 0) + 1
print("source_kind 分布:", kinds)
