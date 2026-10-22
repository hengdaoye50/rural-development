"""One-shot: normalize all area CHECK/NOT NULL fields before build_db."""
from __future__ import annotations

import csv
import re
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
PREC = {"day", "month", "year", "unknown"}
STATE = {"active", "superseded", "withdrawn"}
TYPE = {f"T0{i}" for i in range(1, 9)}
DATE = re.compile(r"^\d{4}(-\d{2}){0,2}$")
YMD = re.compile(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$")
REGION = re.compile(r"^[1-8]\d{5}$")
SRC = re.compile(r"^S\d+$")


def prec_of(ymd: str) -> str:
    m = YMD.match(ymd or "")
    if not m:
        return "unknown"
    if m.group(3):
        return "day"
    if m.group(2):
        return "month"
    return "year"


def fix_row(r: dict) -> dict:
    for k in list(r):
        if r[k] is None:
            r[k] = ""
    # type
    if r.get("type_code") not in TYPE:
        r["type_code"] = "T01"
    # dates: if precision holds a date, move it
    prec = (r.get("founded_precision") or "").strip()
    ymd = (r.get("founded_ymd") or "").strip()
    if prec and DATE.match(prec) and not DATE.match(ymd):
        r["founded_ymd"] = prec
        r["founded_precision"] = prec_of(prec)
    elif ymd and DATE.match(ymd):
        r["founded_precision"] = prec_of(ymd)
    elif not ymd:
        if prec in PREC:
            pass
        elif DATE.match(prec):
            r["founded_ymd"] = prec
            r["founded_precision"] = prec_of(prec)
        else:
            r["founded_precision"] = "unknown"
    else:
        r["founded_precision"] = "unknown"
        r["founded_ymd"] = ""
    if r.get("founded_precision") not in PREC:
        r["founded_precision"] = prec_of(r.get("founded_ymd") or "") or "unknown"

    # status: may have org text or precision
    st = (r.get("status") or "").strip()
    if st in STATUS:
        pass
    elif st in PREC and (r.get("founded_precision") in PREC):
        # status holds precision value wrongly
        lead = (r.get("lead_org") or "").strip()
        if lead in STATUS:
            r["status"] = lead
            r["lead_org"] = ""
        else:
            r["status"] = "待核"
    elif st:
        # org text in status
        if not (r.get("lead_org") or "").strip():
            r["lead_org"] = st
        r["status"] = "待核"
    else:
        r["status"] = "待核"

    if r.get("record_state") not in STATE:
        if (r.get("record_state") or "").startswith("S"):
            r["first_source_id"] = r["record_state"]
        r["record_state"] = "active"

    if not (r.get("created_by") or "").strip():
        r["created_by"] = "align-fix"
    if not (r.get("created_at") or "").strip():
        r["created_at"] = "2026-09-30"
    if not (r.get("updated_at") or "").strip():
        r["updated_at"] = r["created_at"]

    # county_code required
    if not (r.get("county_code") or "").strip():
        r["county_code"] = r.get("city_code") or r.get("province_code") or "000000"
    for col in ("province_code", "city_code"):
        if not (r.get(col) or "").strip():
            cc = r.get("county_code") or ""
            r[col] = cc[:2] + "0000" if cc else "000000"

    if not (r.get("name") or "").strip():
        r["name"] = r.get("area_id") or "未命名"
    if not (r.get("name_norm") or "").strip():
        r["name_norm"] = r["name"]
    if not (r.get("cover_desc") or "").strip():
        r["cover_desc"] = r.get("summary") or r.get("name") or "见来源"

    if r.get("first_source_id") and not SRC.match(r["first_source_id"]):
        r["first_source_id"] = ""
    return r


def main() -> int:
    n = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        fields = list(rows[0].keys())
        out = []
        for r in rows:
            before = dict(r)
            r = fix_row(r)
            if r != before:
                n += 1
            out.append(r)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            w.writerows(out)
    print("normalized", n)
    return n


if __name__ == "__main__":
    main()
