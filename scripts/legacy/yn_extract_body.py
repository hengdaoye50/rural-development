# -*- coding: utf-8 -*-
"""一次性：把已确认的云南省级名单页抽成结构化政策记录，append 到 POL-YN-ROSTER-policy.jsonl。"""
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
        raise SystemExit("no body div")
    lines: list[str] = []
    for el in d.find_all(["p", "div", "h1", "h2", "h3", "h4", "table", "tr"], recursive=True):
        if el.name in ("div",) and el.find(["p", "div"]):
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
        if el.name.startswith("h") or (strong and strong.get_text(strip=True) == t):
            lines.append("## " + t)
        else:
            lines.append(t)
    # collapse duplicate consecutive lines
    out: list[str] = []
    for ln in lines:
        if out and out[-1] == ln:
            continue
        out.append(ln)
    return "\n\n".join(out)


def cn(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5]", text))


def append(rec: dict) -> None:
    with open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"appended: {rec['title']}  chars={rec['full_text_chars']}")


if __name__ == "__main__":
    url = sys.argv[1]
    md = body_md(url)
    print(md[:600])
    print("...TOTAL CHARS", cn(md))
    if len(sys.argv) > 2 and sys.argv[2] == "--dump":
        open("tmp_body.md", "w", encoding="utf-8").write(md)
