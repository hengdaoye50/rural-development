# -*- coding: utf-8 -*-
"""临安区「耕织未来片区」候选表（杭州片区资源清单 · 临安）。"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-ZJ-hz2026b.csv"
SNAP = ROOT / "data" / "raw" / "ZJ" / "2026-hz-resource-lists" / "linan.md"

URL = "https://www.sohu.com/a/1064015905_121117483"
TITLE = "乡村片区组团发展｜杭州市临安区片区资源清单"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    excerpt = ""
    for line in SNAP.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if "耕织未来片区" in s and len(s) >= 40:
            excerpt = s[:200]
            break
    row = {
        "name": "耕织未来片区", "type_code": "T01", "city_code": "330100", "county_code": "330112",
        "cover_desc": "位于临安区，以光明村为重点村，区域面积63.6平方公里（据《杭州市片区资源清单》）",
        "status": "待核", "founded_ymd": "", "founded_precision": "unknown",
        "issuer": "杭州农业农村", "summary": "",
        "source_url": URL, "source_title": TITLE, "publisher": "杭州农业农村（搜狐转载）",
        "published_ymd": "", "credibility": "B", "excerpt": excerpt,
        "local_path": "data/raw/ZJ/2026-hz-resource-lists/linan.md",
    }
    cols = list(row.keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerow(row)
    tmp.replace(OUT)
    print(f"1 条 -> {OUT.relative_to(ROOT)}｜excerpt {len(excerpt)} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
