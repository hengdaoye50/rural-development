# -*- coding: utf-8 -*-
"""把人工确认干净的粤陕片区落成候选表（运行中）。

名单（逐条核对过原文）：
  GD 清城区源潭镇高桥黄溪片区
  SN 彬州市义门镇罗店村片区
  SN 汉台区武乡镇吴庄村片区
  SN 汉中市汉台区河东店镇花果村片区
  SN 合阳县新池镇薯乡共富片区
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(".")
KEEP = {
    "GD": [("清城区源潭镇高桥黄溪片区", "441802", "清远市清城区源潭镇，高桥、黄溪两村连片")],
    "SN": [
        ("彬州市义门镇罗店村片区", "610482", "咸阳市彬州市义门镇罗店村为核心的美丽村庄片区"),
        ("汉台区武乡镇吴庄村片区", "610702", "汉中市汉台区武乡镇吴庄村美丽村庄片区"),
        ("汉中市汉台区河东店镇花果村片区", "610702", "汉中市汉台区河东店镇花果村美丽村庄片区"),
        ("合阳县新池镇薯乡共富片区", "610524", "渭南市合阳县新池镇，红薯产业共富片区"),
    ],
}
CITY = {"44": "440000", "61": "610000"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ext = list(csv.DictReader(open("data/stage/candidates/gd-sn-extract.csv", encoding="utf-8-sig")))
    by_name: dict[str, dict] = {}
    for r in ext:
        by_name.setdefault(r["name"], r)

    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status",
            "founded_ymd", "founded_precision", "issuer", "summary", "source_url",
            "source_title", "publisher", "published_ymd", "credibility", "excerpt", "local_path"]
    for abbr, items in KEEP.items():
        rows = []
        for name, code, cover in items:
            hit = None
            for k, v in by_name.items():
                if name in k or k in name:
                    hit = v
                    break
            if not hit:
                print(f"!! 没有来源页：{name}")
                continue
            rows.append({
                "name": name, "type_code": "T01", "city_code": CITY[code[:2]],
                "county_code": code, "cover_desc": cover, "status": "运行中",
                "founded_ymd": "", "founded_precision": "unknown",
                "issuer": "广东省农业农村厅" if abbr == "GD" else "陕西省农业农村厅",
                "summary": "", "source_url": hit["url"], "source_title": hit["title"],
                "publisher": "广东省农业农村厅" if abbr == "GD" else "陕西省农业农村厅",
                "published_ymd": "", "credibility": "B",
                "excerpt": hit["excerpt"],
                "local_path": hit["local_path"].rstrip("/") + "/原文.md",
            })
        out = ROOT / f"data/stage/candidates/area-media-roster-{abbr}-gdsn.csv"
        tmp = out.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
        tmp.replace(out)
        print(f"{abbr}: {len(rows)} 条 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
