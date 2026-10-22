"""从 JS-batch02-candidates 重写 A320051+ 规范行。"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "stage" / "JS-batch02-candidates.csv"
OUT = ROOT / "data" / "clean" / "by_province" / "JS-area.csv"
SRC_OUT = ROOT / "data" / "clean" / "by_province" / "JS-source.csv"
MAP_OUT = ROOT / "data" / "clean" / "by_province" / "JS-area_source_map.csv"

HEADER = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision",
    "status", "lead_org", "issuer", "summary", "parent_area_key",
    "first_source_id", "record_state", "created_at", "updated_at", "created_by",
]


def precision_of(ymd: str) -> str:
    if len(ymd) >= 10:
        return "day"
    if len(ymd) >= 7:
        return "month"
    if ymd:
        return "year"
    return "unknown"


def main() -> None:
    cands = list(csv.DictReader(STAGE.open(encoding="utf-8-sig", newline="")))
    # 只取 include_area
    areas = []
    sources = []
    maps = []
    existing = list(csv.DictReader(OUT.open(encoding="utf-8-sig", newline="")))
    exist_by_name = {r.get("name"): r for r in existing}

    next_a = 51
    next_s = 31
    seen = set()
    for c in cands:
        if (c.get("include_decision") or "") not in ("include_area", ""):
            # 容错：有的行错位
            if c.get("exclude_code") == "include_area" or c.get("area_or_belt") == "area":
                pass
            else:
                continue
        if c.get("area_or_belt") and c["area_or_belt"] != "area":
            continue
        name = (c.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)

        # 修复候选行错位：include_decision 像地区名
        lead = (c.get("lead_org") or "").strip()
        ymd = (c.get("founded_ymd") or "").strip()
        decision = (c.get("include_decision") or "").strip()
        issuer = ""
        if re.match(r"^20\d{2}", lead) and not ymd:
            ymd, lead = lead, ""
        if decision.endswith("县") or decision.endswith("市") or decision.endswith("区"):
            if not lead:
                lead = decision
            decision = "include_area"

        if decision not in ("include_area", "include_belt", ""):
            continue

        cover = (c.get("cover_desc") or "").strip()
        towns = (c.get("towns_or_villages") or "").strip()
        m = re.search(r"(\d+)\s*个?", cover + towns + name + (c.get("excerpts") or ""))
        scale_v = m.group(1) if m and "村" in (cover + towns + c.get("excerpts") or "") else ""

        # name_norm
        name_norm = re.sub(r"(省|市|县|区|片区|示范片区|乡村振兴)", "", name) or name
        name_norm = name_norm.strip("·• ") or name

        sid = f"S32{next_s:04d}"
        next_s += 1
        aid = f"A32{next_a:04d}"
        next_a += 1

        row = {
            "area_id": aid,
            "name": name,
            "name_norm": name_norm,
            "type_code": (c.get("type_hint") or "T01").strip() or "T01",
            "type_primary_note": (c.get("note") or "")[:80],
            "tags": "和美乡村",
            "province_code": c.get("province_code") or "320000",
            "city_code": c.get("city_code") or "",
            "county_code": c.get("county_code") or "",
            "town_codes": towns,
            "cover_desc": cover or (c.get("excerpts") or "")[:80],
            "scale_villages": scale_v,
            "scale_towns": "",
            "founded_ymd": ymd,
            "founded_precision": precision_of(ymd),
            "status": "待核" if (c.get("cred") == "D" or not ymd) else "运行中",
            "lead_org": lead,
            "issuer": lead,
            "summary": (c.get("excerpts") or "")[:200],
            "parent_area_key": "",
            "first_source_id": sid,
            "record_state": "active",
            "created_at": (c.get("fetched_at") or "2026-09-29T12:00:00+08:00")[:19],
            "updated_at": (c.get("fetched_at") or "2026-09-29T12:00:00+08:00")[:19],
            "created_by": "JS-batch02-repair",
        }
        # 已存在同名则更新关键字段，不新建
        if name in exist_by_name:
            old = exist_by_name[name]
            aid = old["area_id"]
            row["area_id"] = aid
            sid = old.get("first_source_id") or sid
            row["first_source_id"] = sid
            exist_by_name[name] = row
            areas.append(row)
        else:
            areas.append(row)
            exist_by_name[name] = row

        sources.append({
            "source_id": sid,
            "area_id": aid,
            "url": c.get("url") or "",
            "title": c.get("title") or name,
            "publisher": c.get("publisher") or "",
            "published_ymd": c.get("published_ymd") or "",
            "excerpt": (c.get("excerpts") or "")[:500],
            "fetched_at": c.get("fetched_at") or "2026-09-29T12:00:00+08:00",
            "credibility": c.get("cred") or "B",
            "local_path": "",
            "hash_sha256": "",
        })
        maps.append({
            "area_id": aid,
            "source_id": sid,
            "entity_type": "area",
            "rel": "primary",
        })

    # 合并进 JS-area：保留原有其他行 + 替换/新增 batch02
    by_id = {r["area_id"]: r for r in existing}
    for r in areas:
        by_id[r["area_id"]] = r
    rows = [by_id[k] for k in sorted(by_id)]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in HEADER})
    print("JS-area", len(rows))

    sh = ["source_id", "area_id", "url", "title", "publisher", "published_ymd", "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256"]
    sexist = []
    if SRC_OUT.exists():
        sexist = list(csv.DictReader(SRC_OUT.open(encoding="utf-8-sig", newline="")))
    sidset = {r["source_id"] for r in sexist}
    for s in sources:
        if s["source_id"] not in sidset:
            sexist.append(s)
            sidset.add(s["source_id"])
    with SRC_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sh, extrasaction="ignore")
        w.writeheader()
        for r in sexist:
            w.writerow({h: r.get(h, "") for h in sh})
    print("JS-source", len(sexist))

    mh = ["area_id", "source_id", "entity_type", "rel"]
    mexist = []
    if MAP_OUT.exists():
        mexist = list(csv.DictReader(MAP_OUT.open(encoding="utf-8-sig", newline="")))
    keys = {(r["area_id"], r["source_id"]) for r in mexist}
    for m in maps:
        if (m["area_id"], m["source_id"]) not in keys:
            mexist.append(m)
    with MAP_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=mh, extrasaction="ignore")
        w.writeheader()
        w.writerows(mexist)
    print("JS-map", len(mexist))


if __name__ == "__main__":
    main()
