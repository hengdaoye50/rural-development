"""Normalize founded_precision and clear residual field pollution."""
from __future__ import annotations

import csv
import re
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
LEAK = {"repair-2026-09", "XZ-batch01", "YN-batch01", "JS-batch01", "SD-batch01", "ZJ-batch01"}
TS = re.compile(r"^\d{4}-\d{2}-\d{2}T")


def main() -> None:
    n = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = list(rows[0].keys())
        for r in rows:
            ymd = (r.get("founded_ymd") or "").strip()
            if ymd:
                if re.match(r"^\d{4}-01-01$", ymd):
                    r["founded_precision"] = "year"
                elif re.match(r"^\d{4}-\d{2}-01$", ymd):
                    r["founded_precision"] = "month"
                elif re.match(r"^\d{4}-\d{2}-\d{2}$", ymd):
                    r["founded_precision"] = "day"
                elif re.match(r"^\d{4}$", ymd):
                    r["founded_precision"] = "year"
                elif re.match(r"^\d{4}-\d{2}$", ymd):
                    r["founded_precision"] = "month"
            for col in ("lead_org", "issuer", "parent_area_key"):
                v = (r.get(col) or "").strip()
                if v in LEAK or TS.match(v) or re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                    r[col] = ""
                    n += 1
            # issuer 残留长摘要（应是单位名，短）
            for col in ("lead_org", "issuer"):
                v = r.get(col) or ""
                if len(v) > 80:
                    # 长文本更像 summary 漏进来了；若 summary 空则归位
                    if not (r.get("summary") or "").strip():
                        r["summary"] = v
                    r[col] = ""
                    n += 1
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print("cleaned", n)


if __name__ == "__main__":
    main()
