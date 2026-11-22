# -*- coding: utf-8 -*-
"""修正「市码填进 county_code、city_code 填成省码」的错位（幂等，先 --dry-run）。

现象：`county_code` 是地级市码、`city_code` 是省码，例如陕西渭南：
  city_code=610000（陕西省）、county_code=610500（渭南市）
成因是早期入库按「市→县」两列错位写。这类单元本身是**市域级片区**（跨县），
正确写法是：`city_code=旧 county_code`、`county_code` 同填该市级码（`county_code` 是 NOT NULL，
直辖市/直筒子市也用这个约定）、`admin_level='city'`。

只写 `data/clean/by_province/*-area.csv`。区划归属行（area_region_map）保留原市级码，
role 仍记 `county`（现有约定：直筒子市/市域单元用市级码 + role=county）。

用法：
  python scripts/fix_city_county_shift.py --dry-run
  python scripts/fix_city_county_shift.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)


def read(p: Path):
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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    lvl = {r["region_code"]: r["level"] for r in con.execute("select region_code, level from region")}
    rows = [dict(r) for r in con.execute("""
        select area_id, name, province_code, city_code, county_code, admin_level
        from area where record_state='active'""")]
    con.close()

    targets = []
    for r in rows:
        city_lv = lvl.get(r["city_code"] or "")
        county_lv = lvl.get(r["county_code"] or "")
        # 错位特征：city 是省级、county 是市级（或省级）
        if city_lv == "province" and county_lv in ("city", "province") and r["county_code"]:
            targets.append(r)
    print(f"市/县码错位：{len(targets)} 条")
    for r in targets[:8]:
        print(f"  {r['area_id']} {r['name'][:30]}｜city {r['city_code']}×county {r['county_code']}")

    ids = {r["area_id"]: r for r in targets}
    today = date.today().isoformat()
    changed = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, arows = read(p)
        hit = [r for r in arows if r.get("area_id") in ids]
        if not hit:
            continue
        changed += len(hit)
        print(f"  {p.name}: {len(hit)}")
        if dry:
            continue
        for r in hit:
            old = ids[r["area_id"]]
            r["city_code"] = old["county_code"]      # 真实地级市码
            # county_code 是 NOT NULL：市域级单元按现有约定（直辖市/直筒子市）填市级码
            r["county_code"] = old["county_code"]
            r["admin_level"] = "city"
            r["updated_at"] = today
        write(p, hdr, arows)
    print(f"共改 {changed} 条" + ("（dry-run 未写盘）" if dry else ""))
    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
