# -*- coding: utf-8 -*-
"""一次性探针：翻云南省级厅局栏目分页，按关键词筛标题。
用法: python scripts/legacy/yn_scan_col.py <column_base_url> <lo> <hi> [keyword_re]
"""
from __future__ import annotations

import re
import sys
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

DEFAULT_KEY = r"乡村振兴|示范园|田园综合体|百千万|和美乡村|认定名单|名单|片区|组团|先导|示范区|创建名单|验收"


def page(base: str, n: int) -> list[tuple[str, str, str]]:
    u = base if n == 0 else f"{base}index_{n}.html"
    r = requests.get(u, headers=H, timeout=30, verify=False)
    r.encoding = "utf-8"
    s = BeautifulSoup(r.text, "html.parser")
    d = s.select_one("div.scroll_wrap") or s.select_one("div.list") or s.select_one("ul.list")
    out = []
    if not d:
        return out
    for li in d.select("li"):
        a = li.find("a")
        if not a:
            continue
        spans = li.find_all("span")
        dt = spans[-1].get_text(strip=True) if len(spans) > 1 else ""
        if not re.match(r"\d{4}-\d{2}-\d{2}", dt):
            m = re.search(r"\d{4}-\d{2}-\d{2}", li.get_text(" ", strip=True))
            dt = m.group(0) if m else ""
        out.append((a.get_text(strip=True), urljoin(u, a.get("href") or ""), dt))
    return out


if __name__ == "__main__":
    base = sys.argv[1]
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    key = re.compile(sys.argv[4] if len(sys.argv) > 4 else DEFAULT_KEY)
    for n in range(lo, hi + 1):
        try:
            rows = page(base, n)
        except Exception as e:
            print(f"[p{n}] ERR {e}", file=sys.stderr)
            continue
        if not rows:
            print(f"[p{n}] empty, stop", file=sys.stderr)
            break
        print(f"[p{n}] {rows[0][2]} .. {rows[-1][2]} ({len(rows)})", file=sys.stderr)
        for t, u, d in rows:
            if key.search(t):
                print(f"{d}\t{t}\t{u}")
