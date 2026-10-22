"""Deeper quality pass: time from stronger patterns + scale from text.

Rules: never invent. Only write year/month/day when the text explicitly
states a founding/establishment/announcement date for THAT unit.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY = ROOT / "data" / "clean" / "by_province"
CLEAN = ROOT / "data" / "clean"

# explicit founding cues
FOUNDED_CUES = re.compile(
    r"(成立|设立|挂牌|获批|入选|命名|印发|启动|创建|开园|授牌|认定|公布|签约|组建)"
)
# document number year e.g. 辽农领办〔2023〕13号
DOCNO = re.compile(r"[〔\[（(](20[12]\d)[〕\]）)]")
YEAR_CN = re.compile(r"(20[12]\d)年")
YM_CN = re.compile(r"(20[12]\d)年(\d{1,2})月")
YMD_CN = re.compile(r"(20[12]\d)年(\d{1,2})月(\d{1,2})日")
# scale
VILLAGE = re.compile(r"(\d+)\s*(?:个)?(?:行政)?村")
VILLAGE2 = re.compile(r"(\d+)\s*村")
TOWN = re.compile(r"(\d+)\s*(?:个)?乡?镇")
BATCH = re.compile(r"第([一二三四五六七八九十\d]+)批")

BATCH_YEAR = {
    # conservative: only when text itself has a year near 首批/第二批
}


def pick_time(blob: str) -> tuple[str, str]:
    """Return (founded_ymd, precision) or ('','unknown')."""
    if not blob:
        return "", "unknown"
    m = YMD_CN.search(blob)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}", "day"
    m = YM_CN.search(blob)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        return f"{y:04d}-{mo:02d}-01", "month"
    # founding-adjacent year only
    for m in YEAR_CN.finditer(blob):
        y = int(m.group(1))
        window = blob[max(0, m.start() - 12) : m.end() + 20]
        if FOUNDED_CUES.search(window) or "年以来" in window or "当年" in window:
            return f"{y:04d}-01-01", "year"
    # document number is a strong founding/issuing signal
    m = DOCNO.search(blob)
    if m:
        y = int(m.group(1))
        return f"{y:04d}-01-01", "year"
    return "", "unknown"


def pick_scale(blob: str) -> tuple[str, str]:
    if not blob:
        return "", ""
    villages = ""
    towns = ""
    m = VILLAGE.search(blob) or VILLAGE2.search(blob)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 500:
            villages = str(n)
    m = TOWN.search(blob)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 50:
            towns = str(n)
    return villages, towns


def load_sources() -> dict[str, str]:
    out = {}
    for p in sorted(BY.glob("*-source.csv")):
        for r in csv.DictReader(p.open(encoding="utf-8-sig", newline="")):
            out[r.get("source_id") or ""] = " ".join(
                [
                    r.get("title") or "",
                    r.get("excerpt") or "",
                    r.get("published_ymd") or "",
                ]
            )
    return out


def main() -> None:
    sources = load_sources()
    t_fixed = s_fixed = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = list(rows[0].keys())
        n = 0
        for r in rows:
            blob = " ".join(
                [
                    r.get("type_primary_note") or "",
                    r.get("cover_desc") or "",
                    r.get("summary") or "",
                    sources.get(r.get("first_source_id") or "", ""),
                ]
            )
            # time
            need_t = not r.get("founded_ymd") or r.get("founded_precision") in (
                "",
                "unknown",
            )
            if need_t:
                ymd, prec = pick_time(blob)
                if ymd:
                    r["founded_ymd"] = ymd
                    r["founded_precision"] = prec
                    n += 1
                    t_fixed += 1
            # scale
            if not r.get("scale_villages") and not r.get("scale_towns"):
                v, t = pick_scale(blob)
                if v or t:
                    r["scale_villages"] = v
                    r["scale_towns"] = t
                    n += 1
                    s_fixed += 1
        if n:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
            print(f"{p.name}: fixed {n}")
    print(f"total time {t_fixed}, scale {s_fixed}")


if __name__ == "__main__":
    main()
