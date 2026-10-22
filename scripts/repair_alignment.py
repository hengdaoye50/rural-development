"""修复 by_province/*-area.csv 字段错位（tags 逗号拆列 / 空字段被吞导致右移）。

已对齐的行原样跳过，避免把 founded_ymd 误判成 created_at。
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"

HEADER = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision",
    "status", "lead_org", "issuer", "summary", "parent_area_key",
    "first_source_id", "record_state", "created_at", "updated_at", "created_by",
]

STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
PRECISION = {"day", "month", "year", "unknown"}
STATE = {"active", "superseded", "withdrawn"}
TYPE_CODES = {f"T0{i}" for i in range(1, 9)}
BATCH = re.compile(r"^[A-Z]{2}-batch\d+$")
AREA_ID = re.compile(r"^A\d{6}$")
SOURCE_ID = re.compile(r"^S\d+$")
REGION = re.compile(r"^[1-8]\d{5}$")
TS = re.compile(r"^\d{4}-\d{2}-\d{2}")
DATE = re.compile(r"^\d{4}(-\d{2}){0,2}$")

FREE = [
    "name", "name_norm", "type_primary_note", "tags",
    "town_codes", "cover_desc", "scale_villages", "scale_towns",
    "founded_ymd", "lead_org", "issuer", "summary", "parent_area_key",
]


def _row_wellformed(vals: list[str]) -> bool:
    """整行已是 HEADER 矩形且锚点字段合法 → 不需要 realign。"""
    if len(vals) != len(HEADER):
        return False
    row = dict(zip(HEADER, vals))
    if not AREA_ID.match(row.get("area_id") or ""):
        return False
    if row.get("type_code") not in TYPE_CODES:
        return False
    if row.get("status") not in STATUS:
        return False
    if row.get("founded_precision") not in PRECISION:
        return False
    if row.get("record_state") not in STATE:
        return False
    if not SOURCE_ID.match(row.get("first_source_id") or ""):
        return False
    for col in ("province_code", "city_code", "county_code"):
        v = row.get(col) or ""
        if v and not REGION.match(v):
            return False
    for col in ("founded_ymd", "created_at", "updated_at"):
        v = row.get(col) or ""
        if v and not DATE.match(v.split("T")[0]):
            return False
    cb = row.get("created_by") or ""
    if cb and not (BATCH.match(cb) or cb.startswith("repair") or "-" in cb):
        return False
    return True


def realign(vals: list[str]) -> dict[str, str]:
    """按语义锚点重排一行。已对齐的行原样返回。"""
    if _row_wellformed(vals):
        return dict(zip(HEADER, vals))

    out = {h: "" for h in HEADER}
    used = [False] * len(vals)

    def take(pred, field, last=False):
        idxs = [i for i, v in enumerate(vals) if not used[i] and pred(v)]
        if not idxs:
            return
        i = idxs[-1] if last else idxs[0]
        used[i] = True
        out[field] = vals[i]

    take(lambda v: bool(AREA_ID.match(v)), "area_id")
    take(lambda v: v in TYPE_CODES, "type_code")
    take(lambda v: v in STATUS, "status")
    take(lambda v: v in PRECISION, "founded_precision")
    take(lambda v: v in STATE, "record_state")
    take(lambda v: bool(BATCH.match(v)), "created_by", last=True)
    take(lambda v: bool(SOURCE_ID.match(v)), "first_source_id")

    # 时间戳：优先原列位，避免偷走 founded_ymd
    i_created, i_updated = HEADER.index("created_at"), HEADER.index("updated_at")
    if len(vals) > i_created and TS.match(vals[i_created] or "") and not used[i_created]:
        used[i_created] = True
        out["created_at"] = vals[i_created]
    if len(vals) > i_updated and TS.match(vals[i_updated] or "") and not used[i_updated]:
        used[i_updated] = True
        out["updated_at"] = vals[i_updated]
    if not out["created_at"] or not out["updated_at"]:
        ts_idxs = [i for i, v in enumerate(vals) if not used[i] and TS.match(v)]
        if not out["created_at"] and ts_idxs:
            used[ts_idxs[0]] = True
            out["created_at"] = vals[ts_idxs[0]]
            ts_idxs = ts_idxs[1:]
        if not out["updated_at"] and ts_idxs:
            used[ts_idxs[0]] = True
            out["updated_at"] = vals[ts_idxs[0]]
            ts_idxs = ts_idxs[1:]
        for i in ts_idxs:
            used[i] = True  # 多余时间戳不要落入 founded_ymd

    # 区划码
    regs = [i for i, v in enumerate(vals) if not used[i] and REGION.match(v)]
    for i, field in zip(regs, ["province_code", "city_code", "county_code"]):
        used[i] = True
        out[field] = vals[i]

    # founded_ymd：剩余日期
    date_idxs = [i for i, v in enumerate(vals) if not used[i] and DATE.match(v) and v != ""]
    if out["founded_precision"] and date_idxs:
        used[date_idxs[0]] = True
        out["founded_ymd"] = vals[date_idxs[0]]

    rest = [vals[i] for i, v in enumerate(vals) if not used[i]]
    if len(rest) > len(FREE):
        extra = len(rest) - len(FREE)
        rest = rest[:3] + [",".join(rest[3 : 3 + 1 + extra])] + rest[3 + 1 + extra :]
    elif len(rest) < len(FREE):
        while len(rest) < len(FREE):
            insert_at = FREE.index("founded_ymd")
            if insert_at > len(rest):
                rest.append("")
            else:
                rest.insert(insert_at, "")

    for k in FREE:
        if out.get(k):
            continue
        if not rest:
            break
        out[k] = rest.pop(0)

    if not out["founded_precision"]:
        out["founded_precision"] = "unknown"
    if not out["status"]:
        out["status"] = "待核"
    if not out["record_state"]:
        out["record_state"] = "active"
    if not out["created_at"]:
        out["created_at"] = "2026-09-28"
    if not out["updated_at"]:
        out["updated_at"] = out["created_at"]
    if not out["created_by"]:
        out["created_by"] = "repair-2026-09"
    if out["county_code"] and not out["province_code"]:
        out["province_code"] = out["county_code"][:2] + "0000"
    if out["province_code"] and not out["city_code"]:
        out["city_code"] = out["province_code"]

    # 后处理：残留错位
    theme = out.get("town_codes", "")
    cover = out.get("cover_desc", "")
    if theme and not re.search(r"(镇|乡|街道|苏木|村)$", theme) and re.search(
        r"(镇|乡|街道|村)$", cover or ""
    ):
        out["tags"] = f"{out['tags']},{theme}" if out.get("tags") else theme
        out["town_codes"] = cover
        out["cover_desc"] = out.get("scale_villages", "")
        out["scale_villages"] = out.get("scale_towns", "")
        out["scale_towns"] = ""
    sv = out.get("scale_villages", "")
    st = out.get("scale_towns", "")
    if len(sv) > 12 and not sv.isdigit():
        m = re.search(r"(\d+)\s*个?村", sv)
        if len(out.get("cover_desc", "")) < 12 or not out.get("cover_desc"):
            out["cover_desc"] = sv
            out["scale_villages"] = m.group(1) if m else (st if st.isdigit() else "")
            if st.isdigit() and not out["scale_villages"]:
                out["scale_villages"] = st
            if out["scale_villages"] == out.get("cover_desc"):
                out["scale_villages"] = m.group(1) if m else ""
            out["scale_towns"] = ""
        elif st.isdigit():
            out["scale_villages"] = st
            out["scale_towns"] = ""
    if not out.get("cover_desc"):
        if out.get("scale_villages") and len(out["scale_villages"]) > 8:
            out["cover_desc"] = out["scale_villages"]
            m = re.search(r"(\d+)\s*个?村", out["cover_desc"])
            if m:
                out["scale_villages"] = m.group(1)
        else:
            out["cover_desc"] = out.get("summary") or out.get("name") or "见来源"
    tc = out.get("town_codes", "")
    if tc and not re.search(r"(镇|乡|街道|村|苏木)$", tc):
        if len(tc) <= 6 and not tc.isdigit() and not REGION.match(tc):
            out["tags"] = f"{out['tags']},{tc}" if out.get("tags") else tc
            out["town_codes"] = ""
    if out.get("scale_villages") and out.get("scale_villages") == out.get("scale_towns"):
        out["scale_towns"] = ""
    return out


def fix_file(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0
    data_rows = rows[1:]
    changed = 0
    out_rows = []
    for raw in data_rows:
        vals = [(v if v is not None else "") for v in raw]
        before = list(vals)
        fixed = realign(vals)
        out_rows.append([fixed[h] for h in HEADER])
        if [fixed[h] for h in HEADER] != before[: len(HEADER)] or len(before) != len(HEADER):
            changed += 1
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(out_rows)
    print(f"{path.name}: repaired {changed}/{len(data_rows)}")
    return changed


def main() -> int:
    total = 0
    for p in sorted(BY_PROV.glob("*-area.csv")):
        total += fix_file(p)
    print(f"total repaired {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
