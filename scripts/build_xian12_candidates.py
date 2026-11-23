# -*- coding: utf-8 -*-
"""西安 12 个美丽村庄片区（陕西省人民政府网 2025-07-25）→ 候选表。
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(".")
URL = "https://www.shaanxi.gov.cn/xw/ldx/ds/202507/t20250725_3547035.html"
RAW = ROOT / "data" / "raw" / "SN" / "20250725-xian-12-pianqu"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-SN-xian.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}

# 名称, 县区码
ROWS = [
    ("太乙长安道片区", "610116", "长安区太乙宫街道"),
    ("伴山乐居，漫步石井片区", "610118", "鄠邑区石井街道"),
    ("古骆情缘片区", "610124", "周至县骆峪镇"),
    ("猕香楼观片区", "610124", "周至县楼观镇、马召镇"),
    ("石川关山邑片区", "610114", "阎良区关山街道"),
    ("田园汤苑片区", "610122", "蓝田县汤峪镇"),
    ("秦风汉韵，钟毓武屯片区", "610114", "阎良区武屯街道"),
    ("柒彩玉山片区", "610122", "蓝田县玉山镇"),
    ("穆柯寨传奇片区", "610115", "临潼区穆寨街道"),
    ("华夏源脉，七彩仁宗片区", "610115", "临潼区仁宗街道"),
    ("拾遗，锺源间片区", "610402", "西咸新区大王街道"),
    ("秦岭八村片区", "610113", "西安高新区草堂街道"),
]


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
    key_line = next((x.strip() for x in body.splitlines() if "这12个美丽村庄片区为" in x), "")
    assert key_line, "找不到名单句"
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for name, code, place in ROWS:
        core = name.split("片区")[0]
        if core not in key_line:
            print("!! 原文未点名：", name)
            continue
        rows.append({
            "name": name, "type_code": "T01", "city_code": "610100", "county_code": code,
            "cover_desc": f"{place}，西安市第一批美丽村庄片区（5个以上美丽村庄连片）",
            "status": "运行中", "founded_ymd": "2025", "founded_precision": "year",
            "issuer": "西安市住建局", "summary": "",
            "source_url": URL, "source_title": "【西安】建成十二个美丽村庄片区",
            "publisher": "陕西省人民政府网（转陕西日报）", "published_ymd": "2025-07-25",
            "credibility": "A", "excerpt": key_line[:200],
            "local_path": "data/raw/SN/20250725-xian-12-pianqu/原文.md",
        })
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(OUT)
    print(f"{len(rows)} 条 -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
