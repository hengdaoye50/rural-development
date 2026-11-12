# -*- coding: utf-8 -*-
"""一次性探针：抓云南省厅栏目列表页，打印标题+链接。不参与管线。"""
from __future__ import annotations

import sys
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings()

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def get(url: str, enc: str | None = None) -> str:
    r = requests.get(url, headers=H, timeout=30, verify=False)
    if enc:
        r.encoding = enc
    elif r.encoding in (None, "ISO-8859-1"):
        r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def links(url: str, keyword: str = "", enc: str | None = None) -> None:
    html = get(url, enc)
    soup = BeautifulSoup(html, "html.parser")
    print(f"=== {url} len={len(html)} ===")
    seen = set()
    for a in soup.find_all("a"):
        t = a.get_text(strip=True)
        h = a.get("href") or ""
        if not t or len(t) < 6:
            continue
        if h.startswith("javascript") or h == "#":
            continue
        if keyword and keyword not in t:
            continue
        full = urljoin(url, h)
        if full in seen:
            continue
        seen.add(full)
        print(f"{t}\t{full}")


if __name__ == "__main__":
    url = sys.argv[1]
    kw = sys.argv[2] if len(sys.argv) > 2 else ""
    enc = sys.argv[3] if len(sys.argv) > 3 else None
    links(url, kw, enc)
