# -*- coding: utf-8 -*-
"""把 area 里「带/廊/圈/线」类单元迁到 belt（幂等，先 --dry-run）。

为什么：`docs/01` §3 E07 例外——公开命名但无实体设立的「示范带/廊/圈」应入 `belt`，
不入 `area`。实测 area 里有 127 条这类记录（辽宁示范带、各地景观带等），
混在片区里会污染主统计。

动作（只写 by_province；merge 会重建 master）：
  1. `{ABBR}-belt.csv` 追加记录（`belt_id` 按省续号，`institutional_note` 注明迁入来源与依据）
  2. `{ABBR}-belt_region_map.csv` 复制原 `area_region_map` 行
  3. `{ABBR}-area.csv` / `area_region_map` / `area_source_map` / `area_policy_map` 删除对应行
  4. 迁移单元的 `source.area_id` 改指向新 `belt_id`（docs/02 §来源约定）

用法：
  python scripts/migrate_belt_from_area.py --dry-run
  python scripts/migrate_belt_from_area.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
ABBR = {
    "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
    "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
    "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
    "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
    "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
    "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
    "650000": "XJ",
}
BELT_SUFFIX = [("走廊", "走廊"), ("廊道", "廊"), ("示范带", "带"), ("带", "带"),
               ("示范圈", "圈"), ("圈", "圈"), ("环线", "环"), ("线", "线")]
PAT = re.compile(r"示范带|廊道|走廊|示范圈|环线|景观带|[带廊圈线]$")
BELT_COLS = ["belt_id", "name", "name_norm", "belt_type", "theme", "province_code", "city_code",
             "county_code", "cover_desc", "scale_villages", "scale_towns", "announced_ymd",
             "year_precision", "issuer", "source_id", "summary", "institutional_note",
             "record_state", "created_at", "updated_at", "created_by"]
BRM_COLS = ["belt_id", "region_code", "role", "is_core"]


def read(p: Path):
    if not p.exists():
        return [], []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
    for r in rows:
        assert set(r) <= set(hdr), f"{p.name}: 字段超出表头 {set(r) - set(hdr)}"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def belt_kind(name: str) -> str:
    s = re.sub(r"[（(][^（）()]*[)）]$", "", name or "").strip()
    if s.endswith("示范片") or (s.endswith("片") and not s.endswith("片区")):
        return "片"
    for suf, kind in BELT_SUFFIX:
        if s.endswith(suf):
            return kind
    if "走廊" in s or "廊道" in s:
        return "廊"
    if "示范圈" in s or s.endswith("圈"):
        return "圈"
    return "带"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    targets = [dict(r) for r in con.execute("""
        select area_id, name, name_norm, province_code, city_code, county_code, cover_desc,
               summary, scale_villages, founded_ymd, founded_precision, issuer, first_source_id,
               status, type_code
        from area where record_state='active'""") if PAT.search(r["name"] or "")]

    by_prov: dict[str, list[dict]] = defaultdict(list)
    for t in targets:
        by_prov[ABBR.get(t["province_code"], "")].append(t)
    total = sum(len(v) for v in by_prov.values())
    print(f"待迁移 {total} 条（{len([k for k, v in by_prov.items() if v])} 省）")

    today = date.today().isoformat()
    moves: list[tuple[str, dict]] = []
    for abbr, items in sorted(by_prov.items()):
        moved_ids: set[str] = set()
        if not abbr:
            print("  ! 省份码无法映射，跳过：", items[0]["province_code"])
            continue
        bh, brows = read(BP / f"{abbr}-belt.csv")
        bmh, bmrows = read(BP / f"{abbr}-belt_region_map.csv")
        ah, arows = read(BP / f"{abbr}-area.csv")
        rmh, rmrows = read(BP / f"{abbr}-area_region_map.csv")
        smh, smrows = read(BP / f"{abbr}-area_source_map.csv")
        pmh, pmrows = read(BP / f"{abbr}-area_policy_map.csv")
        seq = max([int(r["belt_id"][3:]) for r in brows if r.get("belt_id", "").startswith("B")] or [0])
        have = {(r.get("name") or "").strip() for r in brows}
        migrated = {m.group(1) for r in brows
                    for m in [re.search(r"由 area (A\d+) 迁入", r.get("institutional_note") or "")] if m}
        ids = {t["area_id"] for t in items}
        for t in items:
            aid = t["area_id"]
            if aid in migrated:  # 上次中断已写入 belt：只补区划行并继续删 area
                bid = next(r["belt_id"] for r in brows
                           if aid in (r.get("institutional_note") or ""))
                for r in [x for x in rmrows if x.get("area_id") == aid]:
                    bmrows.append({"belt_id": bid, "region_code": r.get("region_code", ""),
                                   "role": r.get("role", "county"), "is_core": r.get("is_core", "")})
                moves.append((abbr, {"area_id": aid, "belt_id": bid, "name": t["name"]}))
                moved_ids.add(aid)
                continue
            if (t["name"] or "").strip() in have:
                print(f"  - 已有同名 belt，跳过 {aid} {t['name'][:20]}")
                continue
            seq += 1
            bid = f"B{t['province_code'][:2]}{seq:04d}"
            brows.append({
                "belt_id": bid, "name": t["name"], "name_norm": t["name_norm"],
                "belt_type": belt_kind(t["name"]), "theme": "",
                "province_code": t["province_code"], "city_code": t["city_code"],
                "county_code": t["county_code"] or "",
                "cover_desc": (t["cover_desc"] or t["summary"] or t["name"])[:400],
                "scale_villages": t["scale_villages"] or "", "scale_towns": "",
                "announced_ymd": t["founded_ymd"] or "",
                "year_precision": t["founded_precision"] or "unknown",
                "issuer": t["issuer"] or "", "source_id": t["first_source_id"] or "",
                "summary": t["summary"] or "",
                "institutional_note": f"由 area {t['area_id']} 迁入：名称属带/廊/圈/线，按 docs/01 §3 E07 归 belt",
                "record_state": "active", "created_at": today, "updated_at": today,
                "created_by": "migrate-belt-from-area",
            })
            have.add((t["name"] or "").strip())
            for r in [x for x in rmrows if x.get("area_id") == t["area_id"]]:
                bmrows.append({"belt_id": bid, "region_code": r.get("region_code", ""),
                               "role": r.get("role", "county"), "is_core": r.get("is_core", "")})
            moves.append((abbr, {"area_id": t["area_id"], "belt_id": bid, "name": t["name"]}))
            moved_ids.add(aid)
        if dry:
            continue
        write(BP / f"{abbr}-belt.csv", list(dict.fromkeys((bh or []) + BELT_COLS)), brows)
        write(BP / f"{abbr}-belt_region_map.csv", list(dict.fromkeys((bmh or []) + BRM_COLS)), bmrows)
        write(BP / f"{abbr}-area.csv", ah, [r for r in arows if r.get("area_id") not in moved_ids])
        write(BP / f"{abbr}-area_region_map.csv", rmh, [r for r in rmrows if r.get("area_id") not in moved_ids])
        write(BP / f"{abbr}-area_source_map.csv", smh, [r for r in smrows if r.get("area_id") not in moved_ids])
        if pmh:
            write(BP / f"{abbr}-area_policy_map.csv", pmh, [r for r in pmrows if r.get("area_id") not in moved_ids])

    print(f"迁移 {len(moves)} 条" + ("（dry-run 未写盘）" if dry else ""))
    for abbr, m in moves[:8]:
        print(f"  {m['area_id']} → {m['belt_id']} {m['name'][:28]}")
    if dry:
        return 0
    # 来源归属改指 belt（docs/02 来源约定：belt 来源的 source.area_id 填 belt_id）
    con2 = sqlite3.connect(DB)
    moved = {m["area_id"]: m["belt_id"] for _, m in moves}
    for abbr in {a for a, _ in moves}:
        sh, srows = read(BP / f"{abbr}-source.csv")
        changed = 0
        for s in srows:
            if s.get("area_id") in moved:
                s["area_id"] = moved[s["area_id"]]
                changed += 1
        if changed:
            write(BP / f"{abbr}-source.csv", sh, srows)
            print(f"  {abbr}: {changed} 条来源改指 belt")
    con2.close()
    print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
