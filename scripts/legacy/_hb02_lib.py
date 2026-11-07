# -*- coding: utf-8 -*-
"""HB02 JSONL 写入库：统一清洗正文、追加落盘、即时 flush。"""
import json, os, re

BATCH = os.path.join("data", "stage", "batches", "POL-HB02-policy.jsonl")
OUT = os.path.join("scripts", "legacy", "_hb02_out")
NAV = re.compile(r"(-->|/col/|^首页|^>\s*政府信息公开|^>|当前位置|索引号|信息分类|发布机构|生成日期|^文\s*号|有\s*效\s*性|打印|关闭|信息来源[:：]\s*$|扫一扫|^[0-9A-Z]{8,}/20\d{2}-\d{4,}|^无\s*$|^有效\s*$|^发布日期[:：])")


def body(key, drop_nav=True):
    p = os.path.join(OUT, key + ".md")
    t = open(p, encoding="utf-8").read()
    lines = t.split("\n", 1)
    if lines[0].startswith("http"):
        t = lines[1] if len(lines) > 1 else ""
    if drop_nav:
        keep = []
        for l in t.split("\n"):
            s = l.strip()
            if not s:
                if keep and keep[-1] != "":
                    keep.append("")
                continue
            if NAV.search(s):
                continue
            keep.append(s)
        t = "\n".join(keep).strip()
    else:
        t = t.strip()
    return t


def chars(t):
    return len(re.sub(r"\s", "", t))


_KEYS = ["title", "doc_no", "issuer", "issuer_level", "issued_ymd", "published_ymd", "doc_type",
         "source_kind", "province_code", "city_code", "county_code", "instruments", "scope_desc",
         "target_areas", "budget_wan", "valid_state", "url", "credibility", "summary", "slug",
         "areas", "events", "full_text", "full_text_chars", "fetched_at", "record_state"]


def add(title, url, full_text, issuer, issuer_level, doc_type, source_kind, county_code,
        city_code="", summary="", slug="", areas=None, events=None, instruments="",
        scope_desc="", target_areas="", budget_wan="", valid_state="现行有效",
        credibility="A", doc_no="", issued_ymd="", published_ymd="", province_code="420000"):
    rec = {
        "title": title, "doc_no": doc_no, "issuer": issuer, "issuer_level": issuer_level,
        "issued_ymd": issued_ymd, "published_ymd": published_ymd, "doc_type": doc_type,
        "source_kind": source_kind, "province_code": province_code, "city_code": city_code,
        "county_code": county_code, "instruments": instruments, "scope_desc": scope_desc,
        "target_areas": target_areas, "budget_wan": budget_wan, "valid_state": valid_state,
        "url": url, "credibility": credibility, "summary": summary[:300], "slug": slug,
        "areas": areas or [], "events": events or [], "full_text": full_text,
        "full_text_chars": chars(full_text), "fetched_at": "2026-11-07", "record_state": "active",
    }
    assert list(rec.keys()) == _KEYS, list(rec.keys())
    with open(BATCH, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    print("OK  %-46s %5d  %s" % (title[:44], chars(full_text), url[-46:]))
