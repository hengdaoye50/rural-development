# -*- coding: utf-8 -*-
"""东北三省首批试点片区（已点名部分）候选表。"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-JL-heilongjiang.csv"
SNAP = ROOT / "data" / "raw" / "JL" / "20260921-jilin-pianquhua"

ROWS = [
    # name, city, county, cover, excerpt, source_url, source_title, publisher, local_path
    ("抚松县长白山文旅赋能型片区", "220600", "220621",
     "白山市抚松县东岗镇，长白山文旅赋能型片区，与「五好两宜」试点衔接",
     "抚松县长白山文旅赋能型片区位列其中", 
     "http://mp.weixin.qq.com/s?__biz=Mzg5Mzg1ODExNg==&mid=2247549933&idx=5&sn=5cb562a1ffc1ed0f45a948c1f5eca219",
     "片区化推进宜居宜业和美乡村建设，吉林准备好了", "吉林省乡村振兴（宣传教育中心）"),
    ("蛟河市新站镇粘玉米产业片区", "220200", "220281",
     "吉林市蛟河市新站镇，粘玉米与灵芝种植加工产业集群片区，核心村六家子村",
     "蛟河市新站镇粘玉米和灵芝种植加工产业集群片区",
     "http://mp.weixin.qq.com/s?__biz=Mzg5Mzg1ODExNg==&mid=2247549933&idx=5&sn=5cb562a1ffc1ed0f45a948c1f5eca219",
     "片区化推进宜居宜业和美乡村建设，吉林准备好了", "吉林省乡村振兴（宣传教育中心）"),
    ("磐石市红石砬子抗联文旅赋能片区", "220200", "220284",
     "吉林市磐石市，抗联红色文化 + 乡村旅游的文旅赋能型片区",
     "磐石市红石砬子抗联文旅赋能片区",
     "http://mp.weixin.qq.com/s?__biz=Mzg5Mzg1ODExNg==&mid=2247549933&idx=5&sn=5cb562a1ffc1ed0f45a948c1f5eca219",
     "片区化推进宜居宜业和美乡村建设，吉林准备好了", "吉林省乡村振兴（宣传教育中心）"),
    ("龙井市三合镇G331文旅赋能片区", "222400", "222405",
     "延边州龙井市三合镇，G331 国道文旅赋能试点片区，核心村北兴村",
     "延边州龙井市三合镇北兴村属于G331国道文旅赋能试点片区",
     "http://mp.weixin.qq.com/s?__biz=Mzg5Mzg1ODExNg==&mid=2247549933&idx=5&sn=5cb562a1ffc1ed0f45a948c1f5eca219",
     "片区化推进宜居宜业和美乡村建设，吉林准备好了", "吉林省乡村振兴（宣传教育中心）"),
    ("桦川县农文旅融合片区化试点", "230800", "230826",
     "佳木斯市桦川县，黑龙江省首批片区化乡村振兴试点（农文旅融合方向）",
     "助力桦川县成功入选黑龙江省首批片区化乡村振兴试点",
     "http://mp.weixin.qq.com/s?__biz=MzI1OTIyOTAzMQ==&mid=2247492857&idx=1&sn=37501590bd5caa048158218d76f319e9",
     "赋能乡村振兴 打造示范标杆｜省规划院助力桦川县成功申报首批省级片区化乡村振兴试点",
     "黑龙江省规划院（公众号）"),
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    rows = []
    for name, city, county, cover, excerpt, url, title, pub in ROWS:
        rows.append({
            "name": name, "type_code": "T01", "city_code": city, "county_code": county,
            "cover_desc": cover, "status": "待核", "founded_ymd": "2026", "founded_precision": "year",
            "issuer": "吉林省农业农村厅" if county.startswith("22") else "黑龙江省农业农村厅",
            "summary": "", "source_url": url, "source_title": title, "publisher": pub,
            "published_ymd": "2026-09-21" if county.startswith("22") else "",
            "credibility": "B", "excerpt": excerpt,
            "local_path": ("data/raw/JL/20260921-jilin-pianquhua/原文.md" if county.startswith("22")
                           else "data/raw/HLJ/2026-hc-pianquhua/原文.md"),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for abbr, sel in (("JL", [r for r in rows if r["county_code"].startswith("22")]),
                      ("HLJ", [r for r in rows if not r["county_code"].startswith("22")])):
        p = OUT.with_name(f"area-media-roster-{abbr}-ne.csv")
        tmp = p.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
            w.writeheader()
            w.writerows(sel)
        tmp.replace(p)
        print(f"{len(sel)} 条 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
