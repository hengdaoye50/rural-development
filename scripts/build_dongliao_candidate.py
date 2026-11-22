# -*- coding: utf-8 -*-
"""东辽县朝阳中心村片区（澎湃号·媒体「e东辽」2026-07-21）→ 候选表。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
URL = "https://m.thepaper.cn/newsDetail_forward_33626404"
RAW = ROOT / "data" / "raw" / "JL" / "20260721-dongliao-pianqu"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-JL-dongliao.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    RAW.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, headers=UA, timeout=40)
    r.encoding = r.apparent_encoding or "utf-8"
    html = r.text
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    body = re.sub(r"<[^>]+>", "\n", body)
    body = re.sub(r"[ \t\u3000]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    (RAW / "原文.md").write_text(body, encoding="utf-8")

    anchor = "持续夯实朝阳中心村片区核心引领地位"
    excerpt = ""
    for line in body.splitlines():
        if anchor in line and len(line.strip()) >= 40:
            excerpt = line.strip()[:200]
            break
    if not excerpt:
        for line in body.splitlines():
            if "片区" in line and len(line.strip()) >= 60:
                excerpt = line.strip()[:200]
                break
    assert excerpt, "找不到摘录"

    row = {
        "name": "东辽县朝阳中心村片区", "type_code": "T01", "city_code": "220400",
        "county_code": "220422",
        "cover_desc": "辽源市东辽县安石镇，以朝阳中心村为核心、联动东道村，跨村抱团与红色研学",
        "status": "待核", "founded_ymd": "2026", "founded_precision": "year",
        "issuer": "东辽县", "summary": "",
        "source_url": URL, "source_title": "东辽县创新片区化发展模式 打造和美乡村建设区域示范样板",
        "publisher": "e东辽（澎湃号·媒体）", "published_ymd": "2026-07-21",
        "credibility": "C", "excerpt": excerpt,
        "local_path": "data/raw/JL/20260721-dongliao-pianqu/原文.md",
    }
    cols = list(row.keys())
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerow(row)
    tmp.replace(OUT)
    print("1 条 ->", OUT.relative_to(ROOT), "| excerpt", len(excerpt), "字")
    print(excerpt[:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
