# -*- coding: utf-8 -*-
"""咸阳长武县亭口镇桃园片区（陕西党建网转陕西日报 2026-09-08）→ 候选表。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(".")
URL = "https://www.sx-dj.gov.cn/ztzl/zdjcxczx/2097226357191004161.html"
RAW = ROOT / "data" / "raw" / "SN" / "20260908-xianyang-pianqu"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-SN-xianyang.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    RAW.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, headers=UA, timeout=40)
    r.encoding = r.apparent_encoding or "utf-8"
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
    body = re.sub(r"<[^>]+>", "\n", body)
    body = re.sub(r"[ \t\u3000]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    (RAW / "原文.md").write_text(body, encoding="utf-8")
    line = next((x.strip() for x in body.splitlines() if "组成桃园片区" in x), "")
    assert line, "找不到桃园片区句"
    row = {
        "name": "长武县亭口镇桃园片区", "type_code": "T01", "city_code": "610400",
        "county_code": "610428",
        "cover_desc": "咸阳市长武县亭口镇，山庄、礼村、上孟 3 个采空区搬迁村跨村联建组成桃园片区（桃园社区）",
        "status": "运行中", "founded_ymd": "2026", "founded_precision": "year",
        "issuer": "咸阳市农业农村局", "summary": "",
        "source_url": URL, "source_title": "从一片美到全域兴——咸阳片区化推进乡村振兴观察",
        "publisher": "陕西党建网（转陕西日报）", "published_ymd": "2026-09-08",
        "credibility": "A", "excerpt": line[:200],
        "local_path": "data/raw/SN/20260908-xianyang-pianqu/原文.md",
    }
    cols = list(row.keys())
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerow(row)
    tmp.replace(OUT)
    print("1 条 ->", OUT.relative_to(ROOT), "|", line[:60])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
