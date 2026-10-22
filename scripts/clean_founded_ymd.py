"""清理 founded_ymd / lead_org / issuer 中的非日期与错位。"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY = ROOT / "data" / "clean" / "by_province"
DATE = re.compile(r"^\d{4}(-\d{2}){0,2}$")


def main() -> None:
    total = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        h = list(rows[0].keys())
        n = 0
        for r in rows:
            ymd = (r.get("founded_ymd") or "").strip()
            # 时间戳 → 取日期部分
            m_ts = re.match(r"(\d{4}-\d{2}-\d{2})", ymd)
            if m_ts and not DATE.match(ymd) and "T" in ymd:
                r["founded_ymd"] = ""  # 抓取时间不是设立时间
                ymd = ""
            if ymd and not DATE.match(ymd):
                # 非日期 → 挪到 lead_org/issuer
                blob = ymd
                r["founded_ymd"] = ""
                r["founded_precision"] = "unknown"
                if not r.get("lead_org"):
                    r["lead_org"] = blob
                elif not r.get("issuer"):
                    r["issuer"] = blob
                else:
                    r["type_primary_note"] = (r.get("type_primary_note") or "") + f"；线索:{blob[:40]}"
                n += 1
            # precision 与 ymd 一致
            ymd = r.get("founded_ymd") or ""
            if ymd and DATE.match(ymd):
                if len(ymd) >= 10:
                    r["founded_precision"] = "day"
                elif len(ymd) >= 7:
                    r["founded_precision"] = "month"
                else:
                    r["founded_precision"] = "year"
            elif not ymd:
                if r.get("founded_precision") not in ("unknown", "day", "month", "year"):
                    r["founded_precision"] = "unknown"
                # 若 precision=year 但无 ymd，用 2024-01-01 不如留空
                if r.get("founded_precision") in ("day", "month", "year") and not ymd:
                    # 从 type_primary_note / summary 挖年
                    blob = " ".join(
                        [
                            r.get("type_primary_note") or "",
                            r.get("summary") or "",
                            r.get("cover_desc") or "",
                            r.get("lead_org") or "",
                        ]
                    )
                    m = re.search(r"(20[12]\d)", blob)
                    if m:
                        r["founded_ymd"] = m.group(1)
                        r["founded_precision"] = "year"
                    else:
                        r["founded_precision"] = "unknown"
        if n:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=h)
                w.writeheader()
                w.writerows(rows)
            print(p.name, "fixed ymd", n)
        total += n
    print("total", total)


if __name__ == "__main__":
    main()
