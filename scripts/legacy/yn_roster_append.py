# -*- coding: utf-8 -*-
"""一次性：云南省级名单 -> POL-YN-ROSTER-policy.jsonl（逐条 append，冲突即报错）。"""
from __future__ import annotations

import json
import re
import sys
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
OUT = "data/stage/batches/POL-YN-ROSTER-policy.jsonl"


def body_md(url: str, enc: str = "utf-8") -> str:
    r = requests.get(url, headers=H, timeout=40, verify=False)
    r.encoding = enc
    s = BeautifulSoup(r.text, "html.parser")
    d = s.select_one("div.format") or s.select_one("div.TRS_Editor") or s.select_one("div.article")
    if not d:
        raise SystemExit(f"no body div: {url}")
    lines: list[str] = []
    for el in d.find_all(["p", "div", "h1", "h2", "h3", "h4", "table", "tr"]):
        if el.name == "div" and el.find(["p", "div", "tr"]):
            continue
        if el.name == "tr":
            cells = [c.get_text(" ", strip=True) for c in el.find_all(["td", "th"])]
            if any(cells):
                lines.append("| " + " | ".join(cells) + " |")
            continue
        if el.name == "table":
            continue
        t = el.get_text(" ", strip=True)
        if not t:
            continue
        strong = el.find("strong") or el.find("b")
        if el.name[0] == "h" or (strong and strong.get_text(strip=True) == t):
            lines.append("## " + t)
        else:
            lines.append(t)
    out: list[str] = []
    for ln in lines:
        if out and out[-1] == ln:
            continue
        out.append(ln)
    return "\n\n".join(out)


def cn(t: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5]", t))


def append(rec: dict) -> None:
    rec.setdefault("province_code", "530000")
    rec.setdefault("areas", [])
    rec.setdefault("events", [])
    rec.setdefault("city_code", "")
    rec.setdefault("county_code", "")
    rec.setdefault("target_areas", "")
    rec.setdefault("budget_wan", "")
    rec.setdefault("valid_state", "现行有效")
    rec.setdefault("credibility", "A")
    rec.setdefault("source_kind", "政策文件")
    rec.setdefault("fetched_at", "2026-11-13")
    # 若已有同 url 记录则跳过
    try:
        for ln in open(OUT, encoding="utf-8"):
            if json.loads(ln).get("url") == rec["url"]:
                print(f"skip (duplicate url): {rec['url']}")
                return
    except FileNotFoundError:
        pass
    with open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"appended: {rec['title']} chars={rec['full_text_chars']}")


def build(**kw) -> dict:
    md = body_md(kw["url"], kw.get("enc", "utf-8"))
    if "full_text" in kw:
        raise SystemExit("do not pass full_text manually")
    rec = {k: v for k, v in kw.items() if k != "enc"}
    rec["full_text"] = md
    rec["full_text_chars"] = cn(md)
    return rec


if __name__ == "__main__":
    mod = sys.argv[1]
    spec = json.loads(open(mod, encoding="utf-8").read())
    for item in spec:
        append(build(**item))
