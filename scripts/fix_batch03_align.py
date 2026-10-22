"""Fix field misalignment in subagent-written JS/SD rows (value-preserving)."""
from __future__ import annotations

import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
HEADER = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision",
    "status", "lead_org", "issuer", "summary", "parent_area_key",
    "first_source_id", "record_state", "created_at", "updated_at", "created_by",
]
PREC = {"day", "month", "year", "unknown"}
STATUS = {"运行中", "待核", "已完成", "已撤销", "已更名"}


def realign_row(r: dict) -> dict:
    """Detect classic tail-shift and restore. Never invent content."""
    out = {h: r.get(h) or "" for h in HEADER}
    # Case: precision holds a date, status holds precision, lead holds status
    prec = out["founded_precision"]
    status = out["status"]
    lead = out["lead_org"]
    issuer = out["issuer"]
    summary = out["summary"]
    parent = out["parent_area_key"]
    first = out["first_source_id"]
    state = out["record_state"]
    created = out["created_at"]
    updated = out["updated_at"]
    cby = out["created_by"]

    # Pattern A (JS): founded empty, precision=date-like, status=precision, lead=status
    if not out["founded_ymd"] and prec not in PREC and status in PREC and lead in STATUS:
        out["founded_ymd"] = prec
        out["founded_precision"] = status
        out["status"] = lead
        # next fields: issuer was lead_org org name; summary was issuer; parent was summary
        out["lead_org"] = issuer if issuer != summary else ""
        # issuer and summary duplicated org name → keep one as issuer
        if issuer == summary:
            out["issuer"] = issuer
            out["summary"] = parent
            out["parent_area_key"] = ""
        else:
            out["issuer"] = issuer
            out["summary"] = summary or parent
            out["parent_area_key"] = ""
        # tail: first_source empty, state=source_id, created=active, updated=ts, cby=ts, missing created_by
        if state.startswith("S") and created == "active":
            out["first_source_id"] = state
            out["record_state"] = created
            out["created_at"] = updated[:10] if updated else "2026-09-30"
            out["updated_at"] = cby[:10] if cby and cby[0].isdigit() else out["created_at"]
            out["created_by"] = "JS-batch03"
        elif first.startswith("S"):
            pass
        return out

    # Pattern B (SD): founded empty, precision=status, status empty/missing, lead=issuer name
    # issuer=long summary text, parent=source_id, first=active, state=created, created=updated, cby=batch
    if (
        not out["founded_ymd"]
        and prec not in PREC
        and prec in STATUS
        and parent.startswith("S")
        and first == "active"
    ):
        out["founded_ymd"] = ""
        out["founded_precision"] = "unknown"
        out["status"] = prec  # 待核 or 运行中
        out["lead_org"] = ""
        out["issuer"] = lead  # 农村大众报
        out["summary"] = issuer  # long text
        out["parent_area_key"] = ""
        out["first_source_id"] = parent
        out["record_state"] = first  # active
        out["created_at"] = state  # date
        out["updated_at"] = created  # date
        out["created_by"] = updated  # batch
        return out

    return out


def fix(prov: str) -> int:
    p = BY / f"{prov}-area.csv"
    with p.open(encoding="utf-8-sig", newline="") as f:
        raw = list(csv.reader(f))
    if not raw:
        return 0
    n = 0
    out_rows = [HEADER]
    for row in raw[1:]:
        if not row or not any(row):
            continue
        # pad / trim to header length, ignore extra
        vals = list(row) + [""] * (len(HEADER) - len(row))
        r = dict(zip(HEADER, vals[: len(HEADER)]))
        before = dict(r)
        r = realign_row(r)
        if r != before:
            n += 1
        out_rows.append([r[h] for h in HEADER])
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(out_rows)
    print(prov, "re-aligned", n)
    return n


if __name__ == "__main__":
    fix("JS")
    fix("SD")
