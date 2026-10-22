"""从 source 摘录/标题中抽取年份，回填 area.founded_ymd。"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY = CLEAN / "by_province"

YEAR = re.compile(r"(20[12]\d)年")
YM = re.compile(r"(20[12]\d)年(\d{1,2})月")
YMD = re.compile(r"(20[12]\d)年(\d{1,2})月(\d{1,2})日")


def main() -> None:
    sources = list(csv.DictReader((CLEAN / "source.csv").open(encoding="utf-8-sig", newline="")))
    s_by_id = {s["source_id"]: s for s in sources}
    # 也按 title 索引
    by_title = {}
    for s in sources:
        by_title[s.get("title") or ""] = s

    changed = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = list(rows[0].keys())
        n = 0
        for r in rows:
            if r.get("founded_ymd") and r.get("founded_precision") not in ("", "unknown"):
                continue
            sid = r.get("first_source_id") or ""
            s = s_by_id.get(sid)
            blob = " ".join(
                [
                    r.get("summary") or "",
                    r.get("cover_desc") or "",
                    r.get("type_primary_note") or "",
                    (s or {}).get("excerpt") or "",
                    (s or {}).get("title") or "",
                    (s or {}).get("published_ymd") or "",
                ]
            )
            m = YMD.search(blob)
            if m:
                y, mo, d = m.groups()
                r["founded_ymd"] = f"{y}-{int(mo):02d}-{int(d):02d}"
                r["founded_precision"] = "day"
                n += 1
                changed += 1
                continue
            m = YM.search(blob)
            if m:
                y, mo = m.groups()
                r["founded_ymd"] = f"{y}-{int(mo):02d}"
                r["founded_precision"] = "month"
                n += 1
                changed += 1
                continue
            # 「2024年启动/挂牌/成立」等
            m = re.search(r"(20[12]\d)年[^。]{0,12}(成立|挂牌|启动|设立|创建|印发)", blob)
            if m:
                r["founded_ymd"] = m.group(1)
                r["founded_precision"] = "year"
                n += 1
                changed += 1
        if n:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header)
                w.writeheader()
                w.writerows(rows)
            print(p.name, "time from text", n)
    print("total", changed)


if __name__ == "__main__":
    main()
