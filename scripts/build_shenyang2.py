# -*- coding: utf-8 -*-
"""沈阳 6 个待定片区里能坐实归属的 5 个 → 候选表（待核）。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(".")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
SRC = {
    "438": ("https://nyncj.shenyang.gov.cn/zwgk/fdzdgknr/jyta/zxta/202606/t20260609_5038904.html",
            "data/raw/LN/20260529-shenyang-pianqu/原文.md",
            "市政协十六届五次会议《关于因地制宜发展沈阳新型农村集体经济的提案》（第438号）的答复"),
    "122": ("https://nyncj.shenyang.gov.cn/zwgk/fdzdgknr/jyta/zxta/202201/t20220119_2531541.html",
            "data/raw/LN/20220119-shenyang-tese/原文.md",
            "市政协十五届三次会议《关于强化农业特色产业发展 助力我市乡村振兴提案》（第122号）的答复"),
}
ROWS = [
    ("浑南区东南山区片区", "210112", "浑南区东南部山地", "东南山区山地综合整治项目", "438"),
    ("浑南区棋盘山片区", "210112", "浑南区棋盘山地区", "棋盘山地区土地综合整治项目", "438"),
    ("沈北新区辽河生态片区", "210113", "沈北新区辽河沿线", "辽河生态片区", "438"),
    ("法库县葡萄片区", "210124", "法库县（丁家房等葡萄基地）", "法库丁家房", "122"),
    ("法库县树莓片区", "210124", "法库县（灯仕堡等树莓基地）", "法库灯仕堡", "122"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    texts = {}
    for k, (url, path, title) in SRC.items():
        p = ROOT / path
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            r = requests.get(url, headers=UA, timeout=40)
            r.encoding = r.apparent_encoding or "utf-8"
            body = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
            body = re.sub(r"<[^>]+>", "\n", body)
            body = re.sub(r"[ \t\u3000]+", " ", body)
            body = re.sub(r"\n{3,}", "\n\n", body).strip()
            p.write_text(body, encoding="utf-8")
        texts[k] = (url, path, title, p.read_text(encoding="utf-8"))

    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for name, code, place, anchor, sk in ROWS:
        url, path, title, text = texts[sk]
        excerpt = ""
        for line in text.splitlines():
            s = line.strip()
            if anchor in s and len(s) >= 30:
                excerpt = s[:200]
                break
        if not excerpt:
            print("!! 找不到摘录", name)
            continue
        rows.append({
            "name": name, "type_code": "T01", "city_code": "210100", "county_code": code,
            "cover_desc": f"{place}；归属由沈阳市农业农村局答复与相关文件推定，待官方名单确认",
            "status": "待核", "founded_ymd": "2026", "founded_precision": "year",
            "issuer": "沈阳市农业农村局", "summary": "",
            "source_url": url, "source_title": title, "publisher": "沈阳市农业农村局",
            "published_ymd": "", "credibility": "B", "excerpt": excerpt, "local_path": path,
        })
    out = ROOT / "data/stage/candidates/area-media-roster-LN-shenyang2.csv"
    tmp = out.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(out)
    print(f"{len(rows)} 条 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
