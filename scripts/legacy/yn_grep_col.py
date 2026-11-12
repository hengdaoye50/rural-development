# -*- coding: utf-8 -*-
"""一次性：遍历栏目分页，抓每篇正文，按关键词命中就打印上下文。
用法: python scripts/legacy/yn_grep_col.py <column_base> <lo> <hi> <body_regex>
"""
from __future__ import annotations

import re
import sys
import time
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}


def fetch(u: str) -> BeautifulSoup:
    r = requests.get(u, headers=H, timeout=30, verify=False)
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "html.parser")


def listing(base: str, n: int) -> list[str]:
    u = base if n == 0 else f"{base}index_{n}.html"
    s = fetch(u)
    d = s.select_one("div.scroll_wrap") or s.select_one("div.list") or s.select_one("ul.list")
    if not d:
        return []
    out = []
    for a in d.select("li a"):
        h = a.get("href") or ""
        if ".html" in h:
            out.append(urljoin(u, h))
    return out


if __name__ == "__main__":
    base, lo, hi, pat = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    rx = re.compile(pat)
    seen: set[str] = set()
    for n in range(lo, hi + 1):
        urls = listing(base, n)
        if not urls:
            print(f"[p{n}] empty stop", file=sys.stderr)
            break
        for u in urls:
            if u in seen:
                continue
            seen.add(u)
            try:
                s = fetch(u)
            except Exception as e:
                print("ERR", u, e, file=sys.stderr)
                continue
            d = s.select_one("div.show-content") or s.select_one("div.format") or s.select_one("div.TRS_Editor")
            if not d:
                continue
            t = d.get_text("\n", strip=True)
            hits = rx.findall(t)
            if not hits:
                continue
            title = s.title.get_text(strip=True) if s.title else ""
            print(f"### {title}\n{u}")
            for m in rx.finditer(t):
                seg = t[max(0, m.start() - 220): m.start() + 320].replace("\n", " ")
                print("   ...", seg)
            print()
            time.sleep(0.15)
