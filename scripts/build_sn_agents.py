# -*- coding: utf-8 -*-
"""核验通过的陕西 6 条（杨陵 3 运行中 / 永寿 3 待核 / 旬邑 1 待核）→ 候选表。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(".")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}

# name, county, code, status, url, 锚句（含名字的整句）
ITEMS = [
    ("新集片区", "杨陵区", "610403", "运行中",
     "https://tzcjj.yangling.gov.cn/tzzx/tzdt/2056663850381266946.html",
     "1.新集片区：以新集村、陵湾村为核心示范村"),
    ("姜嫄片区", "杨陵区", "610403", "运行中",
     "https://tzcjj.yangling.gov.cn/tzzx/tzdt/2056663850381266946.html",
     "2.姜嫄片区：以姜嫄村为核心示范村"),
    ("田西片区", "杨陵区", "610403", "运行中",
     "https://tzcjj.yangling.gov.cn/tzzx/tzdt/2056663850381266946.html",
     "3.田西片区：以田西村为核心示范村"),
    ("永寿县苹果片区", "永寿县", "610426", "待核",
     "https://www.yongshou.gov.cn/xwzx/mtjj/202610/t20261015_2124286.html",
     "苹果片区联动店头、常宁、马坊、监军"),
    ("永寿县车厘子片区", "永寿县", "610426", "待核",
     "https://www.yongshou.gov.cn/xwzx/mtjj/202610/t20261015_2124286.html",
     "车厘子片区覆盖监军、永平、常宁"),
    ("永寿县农文旅片区", "永寿县", "610426", "待核",
     "https://www.yongshou.gov.cn/xwzx/mtjj/202610/t20261015_2124286.html",
     "农文旅片区串联48万亩槐林"),
    ("旬邑县职田镇青村、马家堡村片区", "旬邑县", "610429", "待核",
     "https://www.snxunyi.gov.cn/", "拟选择青村、马家堡村片区作为试点"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cache = {}
    rows = []
    for name, county, code, status, url, anchor in ITEMS:
        if url not in cache:
            try:
                r = requests.get(url, headers=UA, timeout=40)
                r.encoding = r.apparent_encoding or "utf-8"
                body = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
                body = re.sub(r"<[^>]+>", "\n", body)
                body = re.sub(r"[ \t\u3000]+", " ", body)
                body = re.sub(r"\n{3,}", "\n\n", body).strip()
            except Exception as e:  # noqa: BLE001
                print("!! 抓取失败", name, e)
                continue
            slug = re.sub(r"[^0-9A-Za-z]+", "-", url.split("//")[1].split("/")[-2] or "page")[:30]
            d = ROOT / "data" / "raw" / "SN" / f"2026-11-23-{slug}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "原文.md").write_text(body, encoding="utf-8")
            cache[url] = (d.relative_to(ROOT), body)
        rel, body = cache[url]
        # 原文常被标签切成多行：允许字间空白
        pat = r"\s*".join(re.escape(ch) for ch in anchor)
        m = re.search(pat, body)
        if not m:
            print("!! 原文无锚句", name)
            continue
        i, j = m.start(), m.end()
        start = max(body.rfind("。", 0, i), body.rfind("\n\n", 0, i)) + 1
        end = body.find("。", j)
        sentence = body[start: end + 1 if end > 0 else j + 60]
        sentence = re.sub(r"\s+", "", sentence)[:200]
        rows.append({
            "name": name, "type_code": "T01", "city_code": "610400", "county_code": code,
            "cover_desc": f"{county}，官方文件/报道点名的片区", "status": status,
            "founded_ymd": "2026", "founded_precision": "year",
            "issuer": "杨陵区投资促进局" if code == "610403" else f"{county}政府",
            "summary": "", "source_url": url, "source_title": "片区化推进乡村全面振兴（报道）",
            "publisher": "杨陵区投资促进局" if code == "610403" else f"{county}政府网",
            "published_ymd": "2026-05-19" if code == "610403" else "",
            "credibility": "B", "excerpt": sentence, "local_path": f"{rel}/原文.md",
        })
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status", "founded_ymd",
            "founded_precision", "issuer", "summary", "source_url", "source_title", "publisher",
            "published_ymd", "credibility", "excerpt", "local_path"]
    out = ROOT / "data/stage/candidates/area-media-roster-SN-agents.csv"
    tmp = out.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(out)
    print(f"{len(rows)} 条 -> {out.relative_to(ROOT)}")
    for r in rows:
        print(" ", r["name"], "|", len(r["excerpt"]), "字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
