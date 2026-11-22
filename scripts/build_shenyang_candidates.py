# -*- coding: utf-8 -*-
"""沈阳 13 个片区里「县区可确定」的部分 → 候选表（来源：沈阳市农业农村局 2026-05-29 答复）。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
URL = "https://nyncj.shenyang.gov.cn/zwgk/fdzdgknr/jyta/zxta/202606/t20260609_5038904.html"
RAWDIR = ROOT / "data" / "raw" / "LN" / "20260529-shenyang-pianqu"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-LN-shenyang.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}

# 名称, 县区码, 所属街道/乡镇, 关键词（在原文中定位句子的锚）
ROWS = [
    ("光辉街道稻米产业片区", "210112", "浑南区光辉街道", "光辉街道稻米产业片区化项目"),
    ("马三家街道西红柿产业片区", "210114", "于洪区马三家街道", "马三家街道西红柿产业片区化项目"),
    ("沈北新区东部林下经济片区", "210113", "沈北新区", "沈北新区东部林下经济片区化项目"),
    ("苏家屯十里河街道畜禽养殖片区", "210111", "苏家屯区十里河街道", "苏家屯十里河街道畜禽养殖片区"),
    ("苏家屯永乐街道设施果蔬片区", "210111", "苏家屯区永乐街道", "苏家屯区永乐街道设施果蔬片区"),
    ("康平县西关屯乡农文旅融合片区", "210123", "康平县西关屯乡", "西关屯乡农文旅融合乡村振兴片区"),
    ("康平县海洲乡花生产业集群片区", "210123", "康平县海洲乡", "海洲乡花生产业集群乡村振兴片区"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    RAWDIR.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, headers=UA, timeout=40)
    r.encoding = r.apparent_encoding or "utf-8"
    html = r.text
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    body = re.sub(r"<[^>]+>", "\n", body)
    body = re.sub(r"[ \t\u3000]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    (RAWDIR / "原文.md").write_text(body, encoding="utf-8")

    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for name, county, place, anchor in ROWS:
        excerpt = ""
        for line in body.splitlines():
            if anchor in line and len(line.strip()) >= 40:
                excerpt = line.strip()[:200]
                break
        if not excerpt:
            print(f"!! 找不到摘录：{name}（锚 {anchor}）")
            continue
        rows.append({
            "name": name, "type_code": "T01", "city_code": "210100", "county_code": county,
            "cover_desc": f"{place}，沈阳市片区化布局中的产业片区（据市农业农村局2026年提案答复）",
            "status": "待核", "founded_ymd": "2026", "founded_precision": "year",
            "issuer": "沈阳市农业农村局", "summary": "",
            "source_url": URL,
            "source_title": "市政协十六届五次会议《关于因地制宜发展沈阳新型农村集体经济的提案》（第438号）的答复",
            "publisher": "沈阳市农业农村局", "published_ymd": "2026-05-29",
            "credibility": "B", "excerpt": excerpt,
            "local_path": "data/raw/LN/20260529-shenyang-pianqu/原文.md",
        })
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(OUT)
    print(f"{len(rows)} 条 -> {OUT.relative_to(ROOT)}")
    for x in rows:
        print(f"  {x['name']}｜{x['county_code']}｜excerpt {len(x['excerpt'])} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
