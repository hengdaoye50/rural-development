# -*- coding: utf-8 -*-
"""生成「杭州片区资源清单」缺失片区的候选表（供 ingest_area_media_roster.py 入库）。

来源：data/raw/ZJ/2026-hz-resource-lists/*.md（公众号原文经浏览器桥落盘 / 搜狐转载）
输出：data/stage/candidates/area-media-roster-ZJ-hz2026.csv
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "ZJ" / "2026-hz-resource-lists"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-ZJ-hz2026.csv"

ART = {
    "yuhang": ("余杭区", "330110", "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650154507&idx=3&sn=fe014a29e71d776dc999c3f1371d81a2",
               "乡村片区组团发展｜杭州市余杭区片区资源清单", "杭州农业农村", "2026-06-04"),
    "qiantang": ("钱塘区", "330114", "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650156448&idx=3&sn=d25bf64853370769198339228a95a13f",
                 "乡村片区组团发展｜杭州市钱塘区片区资源清单", "杭州农业农村", ""),
    "fuyang": ("富阳区", "330111", "http://mp.weixin.qq.com/s?__biz=MzA5ODc5MjIzMQ==&mid=2650157746&idx=3&sn=1c664ca6baa1ddcb4bd326a4118b7c52",
               "乡村片区组团发展｜杭州市富阳区片区资源清单", "杭州农业农村", ""),
    "linping": ("临平区", "330113", "http://mp.weixin.qq.com/s?__biz=Mzg5OTYxNTE1MQ==&mid=2247613610&idx=1&sn=8d6caf060b67fe5c03466ab88de333fe",
                "乡村片区组团发展｜杭州市临平区片区资源清单", "杭州农业农村", ""),
    "tonglu": ("桐庐县", "330122", "https://www.sohu.com/a/1035352717_121106994",
               "片区资源直通车｜杭州市桐庐县", "浙江农业农村（搜狐转载）", "2026-06-11"),
    "jiande": ("建德市", "330182", "https://www.sohu.com/a/1038080877_121106994",
               "片区资源直通车｜建德市", "浙江农业农村（搜狐转载）", ""),
}

# 缺失片区（来自 parse_hz_resource_lists.py 对账结果）
MISSING = [
    ("yuhang", "古城共富片区", "小古城村", "32.6"),
    ("fuyang", "东安诗路片区", "潘堰村", "57.8"),
    ("jiande", "千鹤红片区", "千鹤村", "46.6"),
    ("linping", "塘栖水韵风情片区", "塘栖村", "31.7"),
    ("linping", "运河北片研学共富片区", "新宇村", "14.4"),
    ("qiantang", "沙地弄潮片区", "临江村", "16.7"),
    ("tonglu", "保安源片区", "保安村", "70.0"),
    ("tonglu", "怡源谷片区", "合村村", "76.0"),
    ("tonglu", "云溪畲韵片区", "莪山民族村", ""),
]


def excerpt_for(key: str, name: str, key_village: str) -> str:
    p = SRC / f"{key}.md"
    if not p.exists():
        return ""
    lines = [x.strip() for x in p.read_text(encoding="utf-8").splitlines()]
    for i, s in enumerate(lines):
        if s == name:
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].startswith("片区位于") or name in lines[j]:
                    return lines[j][:200]
    for s in lines:
        if key_village and key_village in s and "重点村" in s:
            return s[:200]
    return ""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for key, name, village, area in MISSING:
        county, code, url, title, publisher, ymd = ART[key]
        cover = f"位于{county}，以{village}为重点村"
        if area:
            cover += f"，区域面积{area}平方公里"
        cover += "（据《杭州市片区资源清单》）"
        rows.append({
            "name": name, "type_code": "T01", "city_code": "330100", "county_code": code,
            "cover_desc": cover, "status": "待核", "founded_ymd": "",
            "founded_precision": "unknown", "issuer": "杭州农业农村", "summary": "",
            "source_url": url, "source_title": title, "publisher": publisher,
            "published_ymd": ymd, "credibility": "B",
            "excerpt": excerpt_for(key, name, village),
            "local_path": f"data/raw/ZJ/2026-hz-resource-lists/{key}.md",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(OUT)
    print(f"{len(rows)} 条 -> {OUT.relative_to(ROOT)}")
    for r in rows:
        print(f"  {r['name']}｜{r['county_code']}｜excerpt {len(r['excerpt'])} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
