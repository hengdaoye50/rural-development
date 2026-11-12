# -*- coding: utf-8 -*-
"""一次性探针：翻云南省农业农村厅「通报公告公示」栏目全部分页，按关键词筛标题。"""
from __future__ import annotations

import json
import re
import sys
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

BASE = "https://nync.yn.gov.cn/zwgk/fdzdgknr/tbgggs/"

KEY = re.compile(r"乡村振兴|示范|田园综合体|百千万|和美乡村|认定|名单|片区|组团|先导|试点|创建|验收|评定|公布")


def page(n: int) -> list[tuple[str, str, str]]:
    u = BASE if n == 0 else f"{BASE}index_{n}.html"
    r = requests.get(u, headers=H, timeout=30, verify=False)
    r.encoding = "utf-8"
    s = BeautifulSoup(r.text, "html.parser")
    d = s.select_one("div.scroll_wrap")
    out = []
    if not d:
        return out
    for li in d.select("li"):
        a = li.find("a")
        if not a:
            continue
        spans = li.find_all("span")
        dt = spans[-1].get_text(strip=True) if len(spans) > 1 else ""
        out.append((a.get_text(strip=True), urljoin(u, a.get("href") or ""), dt))
    return out


if __name__ == "__main__":
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    hits = []
    for n in range(lo, hi + 1):
        try:
            rows = page(n)
        except Exception as e:
            print(f"[p{n}] ERR {e}", file=sys.stderr)
            continue
        if not rows:
            print(f"[p{n}] empty, stop", file=sys.stderr)
            break
        print(f"[p{n}] {rows[0][2]} .. {rows[-1][2]} ({len(rows)})", file=sys.stderr)
        for t, u, d in rows:
            if KEY.search(t):
                hits.append({"title": t, "url": u, "date": d, "page": n})
    json.dump(hits, open("tmp_yn_hits.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for h in hits:
        print(f"{h['date']}\t{h['title']}\t{h['url']}")
