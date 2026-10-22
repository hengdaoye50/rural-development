"""Recover founded dates that got shifted into lead_org/issuer/summary."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY = ROOT / "data" / "clean" / "by_province"

YMD = re.compile(r"(20[12]\d)年(\d{1,2})月(\d{1,2})日")
YM = re.compile(r"(20[12]\d)年(\d{1,2})月")
Y = re.compile(r"(20[12]\d)年")
DATE_ISO = re.compile(r"^(20[12]\d)(?:-(\d{2}))?(?:-(\d{2}))?$")
DOCNO = re.compile(r"[〔\[（(](20[12]\d)[〕\]）)]")
CUE = re.compile(r"(成立|设立|挂牌|获批|入选|命名|印发|启动|创建|开园|授牌|认定|公布|组建)")


def extract(blob: str) -> tuple[str, str]:
    if not blob:
        return "", ""
    m = YMD.search(blob)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", "day"
    m = YM.search(blob)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-01", "month"
    for m in Y.finditer(blob):
        window = blob[max(0, m.start() - 10) : m.end() + 16]
        if CUE.search(window) or "以来" in window:
            return f"{int(m.group(1)):04d}-01-01", "year"
    m = DOCNO.search(blob)
    if m:
        return f"{int(m.group(1)):04d}-01-01", "year"
    return "", ""


def main() -> None:
    total = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = list(rows[0].keys())
        n = 0
        for r in rows:
            need = not (r.get("founded_ymd") or "").strip() or r.get("founded_precision") in (
                "",
                "unknown",
            )
            if not need:
                # 已有日期：校正 precision
                ymd = r.get("founded_ymd") or ""
                m = DATE_ISO.match(ymd)
                if m:
                    if m.group(3):
                        r["founded_precision"] = "day"
                    elif m.group(2):
                        r["founded_precision"] = "month"
                    else:
                        r["founded_precision"] = "year"
                continue

            # 1) lead_org/issuer 以日期开头 → 那是被错位的 founded_ymd
            for col in ("lead_org", "issuer"):
                v = (r.get(col) or "").strip()
                m = re.match(r"^(20[12]\d-\d{2}-\d{2})", v)
                if m:
                    r["founded_ymd"] = m.group(1)
                    r["founded_precision"] = "day"
                    rest = v[len(m.group(1)) :].strip(" T")
                    # 若剩余仍是时间戳则清掉
                    if rest.startswith("20") or not rest:
                        r[col] = ""
                    else:
                        r[col] = rest
                    n += 1
                    break
                m = re.match(r"^(20[12]\d-\d{2})$", v)
                if m:
                    r["founded_ymd"] = m.group(1) + "-01"
                    r["founded_precision"] = "month"
                    r[col] = ""
                    n += 1
                    break
                m = re.match(r"^(20[12]\d)年", v)
                if m and len(v) < 80:
                    # 纯年或年+短语
                    ymd, prec = extract(v[:20])
                    if ymd:
                        r["founded_ymd"] = ymd
                        r["founded_precision"] = prec
                        r[col] = v
                        n += 1
                        break

            if (r.get("founded_ymd") or "").strip():
                continue

            # 2) 从各文本字段抽
            blob = " ".join(
                [
                    r.get("type_primary_note") or "",
                    r.get("cover_desc") or "",
                    r.get("summary") or "",
                    r.get("lead_org") or "",
                    r.get("issuer") or "",
                ]
            )
            ymd, prec = extract(blob)
            if ymd:
                r["founded_ymd"] = ymd
                r["founded_precision"] = prec
                n += 1
                continue

            # 3) created_by 污染在 issuer/lead → 清掉
            for col in ("lead_org", "issuer"):
                if (r.get(col) or "").strip() in {"repair-2026-09"}:
                    r[col] = ""

        if n:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore", lineterminator="\n")
                w.writeheader()
                w.writerows(rows)
            print(f"{p.name}: recovered {n}")
            total += n
    print("total", total)


if __name__ == "__main__":
    main()
