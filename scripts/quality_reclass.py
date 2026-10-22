"""Fix remaining quality issues:
1. ZJ rows with created_by leaked into lead_org/issuer
2. JL 2021 plan-only 示范带 (E07) move area → belt
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(r"D:\CODEX\全国乡村片区化数据库")
BY = ROOT / "data" / "clean" / "by_province"

CREATED_BY_LEAK = {"repair-2026-09", "XZ-batch01", "YN-batch01", "Northwest-batch01"}


def read(p: Path) -> list[dict[str, str]]:
    if not p.exists():
        return []
    return list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))


def write(p: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in fields})


def fix_zj_leak() -> int:
    p = BY / "ZJ-area.csv"
    rows = read(p)
    if not rows:
        return 0
    fields = list(rows[0].keys())
    n = 0
    for r in rows:
        for col in ("lead_org", "issuer", "founded_ymd", "parent_area_key"):
            if (r.get(col) or "").strip() in CREATED_BY_LEAK:
                r[col] = ""
                n += 1
    write(p, fields, rows)
    print(f"ZJ leak cleared {n}")
    return n


# E07: 2021 文旅局规划命名、无设立动作 → belt
JL_TO_BELT = {
    "A220001": ("长吉一体化乡村振兴示范带", "长吉一体化乡村振兴示范带"),
    "A220002": ("吉舒乡村振兴示范带", "吉舒乡村振兴示范带"),
    "A220003": ("吉蛟乡村振兴示范带", "吉蛟乡村振兴示范带"),
    "A220004": ("吉桦乡村振兴示范带", "吉桦乡村振兴示范带"),
    "A220005": ("吉磐乡村振兴示范带", "吉磐乡村振兴示范带"),
}
S220003 = "S220003"

BELT_FIELDS = [
    "belt_id", "name", "name_norm", "belt_type", "theme", "province_code",
    "city_code", "county_code", "cover_desc", "scale_villages", "scale_towns",
    "announced_ymd", "year_precision", "issuer", "source_id", "summary",
    "institutional_note", "record_state", "created_at", "updated_at", "created_by",
]
MAP_FIELDS = ["area_id", "source_id", "entity_type", "rel"]
BELTREG_FIELDS = ["belt_id", "region_code", "role", "is_core"]
SRC_FIELDS = [
    "source_id", "area_id", "url", "title", "publisher", "published_ymd",
    "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256",
]


def move_jl_belts() -> int:
    area_p = BY / "JL-area.csv"
    belt_p = BY / "JL-belt.csv"
    amap_p = BY / "JL-area_source_map.csv"
    bmap_p = BY / "JL-belt_source_map.csv" if False else None
    areg_p = BY / "JL-area_region_map.csv"
    breg_p = BY / "JL-belt_region_map.csv"
    src_p = BY / "JL-source.csv"

    areas = read(area_p)
    if not areas:
        print("no JL area")
        return 0
    afields = list(areas[0].keys())
    keep, moved = [], {}
    for r in areas:
        if r.get("area_id") in JL_TO_BELT:
            moved[r["area_id"]] = r
        else:
            keep.append(r)
    if not moved:
        print("no JL 五带 to move")
        return 0

    belts = read(belt_p) or []
    bfields = list(belts[0].keys()) if belts else BELT_FIELDS
    existing_ids = {b.get("belt_id") for b in belts}
    seq = 1
    for aid, r in moved.items():
        name, name_norm = JL_TO_BELT[aid]
        bid = f"B22{seq:04d}"
        while bid in existing_ids:
            seq += 1
            bid = f"B22{seq:04d}"
        seq += 1
        existing_ids.add(bid)
        belts.append(
            {
                "belt_id": bid,
                "name": name,
                "name_norm": name_norm,
                "belt_type": "带",
                "theme": "乡村振兴",
                "province_code": r.get("province_code") or "220000",
                "city_code": r.get("city_code") or "220200",
                "county_code": r.get("county_code") or "",
                "cover_desc": r.get("cover_desc") or name,
                "scale_villages": r.get("scale_villages") or "",
                "scale_towns": r.get("scale_towns") or "",
                "announced_ymd": "2021",
                "year_precision": "year",
                "issuer": "吉林市文化广播电视和旅游局",
                "source_id": S220003,
                "summary": "吉林市“五带十品百村千宿”工程中的五条乡村振兴示范带之一，拟形成省级示范带。",
                "institutional_note": "E07：2021规划答复命名，未见指挥部/联合党委/分村名单，记belt不入area。",
                "record_state": "active",
                "created_at": "2021-12-29",
                "updated_at": "2026-09-30",
                "created_by": "JL-belt-reclass",
            }
        )

    write(area_p, afields, keep)
    write(belt_p, bfields, belts)

    # source.area_id: point S220003 to a remaining area if any, else first moved's belt
    # Keep source; remap area_source_map from area→belt
    amaps = read(amap_p)
    amaps = [m for m in amaps if m.get("area_id") not in JL_TO_BELT]
    write(amap_p, MAP_FIELDS if not amaps else list(amaps[0].keys()), amaps)

    # belt_region_map: add county/city level mappings from old area_region_map
    aregs = read(areg_p)
    keep_regs = [x for x in aregs if x.get("area_id") not in JL_TO_BELT]
    write(areg_p, list(aregs[0].keys()) if aregs else ["area_id", "region_code", "role", "is_core"], keep_regs)

    bregs = read(breg_p) or []
    bfields_r = list(bregs[0].keys()) if bregs else BELTREG_FIELDS
    # assign region from old area_region_map
    old_reg = {}
    for x in aregs:
        if x.get("area_id") in JL_TO_BELT:
            old_reg[x["area_id"]] = x
    aid_to_bid = {}
    seq = 1
    # rebuild mapping belt ids in order
    for aid in JL_TO_BELT:
        for b in belts:
            if b.get("name") == JL_TO_BELT[aid][0] and b.get("created_by") == "JL-belt-reclass":
                aid_to_bid[aid] = b["belt_id"]
                break
    for aid, bid in aid_to_bid.items():
        src = old_reg.get(aid)
        if src:
            bregs.append(
                {
                    "belt_id": bid,
                    "region_code": src.get("region_code") or "",
                    "role": src.get("role") or "county",
                    "is_core": src.get("is_core") or "1",
                }
            )
    write(breg_p, bfields_r, bregs)

    # area_source_map for belt: belt uses belt_id in source.area_id and area_source_map entity_type
    # also emit belt links in area_source_map (entity_type=belt) per data dict
    amaps2 = read(amap_p)
    for aid, bid in aid_to_bid.items():
        amaps2.append(
            {"area_id": bid, "source_id": S220003, "entity_type": "belt", "rel": "primary"}
        )
    write(amap_p, list(amaps2[0].keys()), amaps2)

    # source.area_id may still point to removed area; fix to first belt
    srcs = read(src_p)
    if srcs:
        sfields = list(srcs[0].keys())
        first_bid = next(iter(aid_to_bid.values()), "")
        for s in srcs:
            if s.get("source_id") == S220003 and s.get("area_id") in JL_TO_BELT:
                s["area_id"] = first_bid
        write(src_p, sfields, srcs)

    print(f"JL moved {len(moved)} area→belt: {list(aid_to_bid.values())}")
    return len(moved)


if __name__ == "__main__":
    fix_zj_leak()
    move_jl_belts()
