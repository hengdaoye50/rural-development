# -*- coding: utf-8 -*-
"""补 `county_code` 空值：按「直辖市/直筒子市/市域单元用市级码」的既有约定填 city_code。

背景：`build_db.py` 把空字符串转成 NULL，而 `area.county_code` 是 NOT NULL；
市域级单元（跨县）没有县码时，按约定填其市级码，而不是留空。

用法：python scripts/repair_empty_county_code.py [--dry-run]
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"


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
    today = date.today().isoformat()
    total = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            if (r.get("county_code") or "").strip():
                continue
            city = (r.get("city_code") or "").strip()
            if not city:
                print(f"  ! {r.get('area_id')} 连 city_code 都空，跳过")
                continue
            r["county_code"] = city
            r["updated_at"] = today
            n += 1
        if n:
            total += n
            print(f"  {p.name}: 补 {n}")
            if not dry:
                write(p, hdr, rows)
    print(f"共补 {total} 条" + ("（dry-run 未写盘）" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
