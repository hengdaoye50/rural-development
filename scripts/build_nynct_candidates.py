# -*- coding: utf-8 -*-
"""省厅 21 篇页面中抽出的新片区 → 候选表（供 ingest_area_media_roster.py 入库）。

输出：data/stage/candidates/area-media-roster-ZJ-nynct2026.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://nynct.zj.gov.cn/col/col1229746526/art/2026/"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-ZJ-nynct2026.csv"

ROWS = [
    # name, county_code, city_code, page, cover, source_title, url
    ("一岭花片区", "330111", "330100", "01",
     "位于富阳区阳陂湖湿地，以农旅融合与稻田景观为特色（据省农业农村厅各地信息）",
     "稻浪翻涌湖生香，杭州市富阳区阳陂湖湿地277亩水稻开始收割",
     BASE + "art_8b82fe4a65ec4bb0941f089935cbd7dd.html"),
    ("观美片区", "330327", "330300", "02",
     "位于苍南县灵溪镇，以“三瓜一稻”稻菜轮作与设施大棚为特色，辐射带动周边9个村社",
     "“三瓜一稻”轮作生金 苍南观美片区走出粮经共富新路",
     BASE + "art_f811399b2481460ca2abd083f230bf94.html"),
    ("三味谷片区", "330902", "330900", "05",
     "位于舟山市定海区白泉镇，“柚香梅林”三味谷片区组团，含皋泄村及周边3个村",
     "舟山市2个村获评今年首批省级重点村",
     BASE + "art_e12fe567635647e5a166472bb0fc21b6.html"),
    ("大莲花片区", "330903", "330900", "05",
     "位于舟山市普陀区朱家尖街道，以大莲花片区组团7个村，联动月岙、白沙等节点",
     "舟山市2个村获评今年首批省级重点村",
     BASE + "art_e12fe567635647e5a166472bb0fc21b6.html"),
    ("西白山共富片区", "330683", "330600", "06",
     "位于嵊州市（西白山区域），以茶园、民宿、研学、露营等运营为特色",
     "嵊州市农业农村局以人才振兴赋能乡村运营提质增效",
     BASE + "art_935a679eb0a744ff9a066ca489bafc69.html"),
    ("赤溪—马站片区", "330327", "330300", "14",
     "苍南县赤溪—马站跨乡镇片区，以中魁村为核心联动周边5村，四季柚与黄金海岸旅游为特色",
     "苍南农业农村局“沙场练兵”正式启动",
     BASE + "art_67a64ed3e6ae4d8f8b4dafbd1a4e0ca4.html"),
]


def excerpt(page: str, key: str) -> str:
    p = ROOT / "data" / "raw" / "ZJ" / "2026-nynct" / f"{page}.md"
    if not p.exists():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        if key in line and "片区" in line:
            return line.strip()[:200]
    return ""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for name, county, city, page, cover, title, url in ROWS:
        key = "赤溪" if name.startswith("赤溪") else name.split("片区")[0]
        rows.append({
            "name": name, "type_code": "T01", "city_code": city, "county_code": county,
            "cover_desc": cover, "status": "待核", "founded_ymd": "", "founded_precision": "unknown",
            "issuer": "浙江省农业农村厅", "summary": "",
            "source_url": url, "source_title": title, "publisher": "浙江省农业农村厅",
            "published_ymd": "", "credibility": "B",
            "excerpt": excerpt(page, key),
            "local_path": f"data/raw/ZJ/2026-nynct/{page}.md",
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
        print(f"  {r['name']}｜{r['county_code']}｜excerpt {len(r['excerpt'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
