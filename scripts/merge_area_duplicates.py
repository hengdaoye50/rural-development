# -*- coding: utf-8 -*-
"""合并重复片区：把 drop 的映射/来源/区划全部挂到 keep，再把 drop 置为 withdrawn。

用法：
  python scripts/merge_area_duplicates.py --keep A370256 --drop A370001 --reason "同一片区，保留市级名单记录"
  python scripts/merge_area_duplicates.py --keep A370256 --drop A370001 --dry-run
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
MAPS = ["area_policy_map", "area_source_map", "area_region_map"]


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", required=True)
    ap.add_argument("--drop", required=True)
    ap.add_argument("--reason", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    keep, drop = args.keep, args.drop
    today = date.today().isoformat()
    moved = 0

    for table in MAPS:
        for p in sorted(BP.glob(f"*-{table}.csv")):
            hdr, rows = read(p)
            if not hdr:
                continue
            existing = {(r.get("area_id"), r.get("entity_type", ""), r.get("policy_id", ""),
                         r.get("source_id", ""), r.get("region_code", ""), r.get("rel", ""))
                        for r in rows if r.get("area_id") == keep}
            changed = False
            out = []
            for r in rows:
                if r.get("area_id") != drop:
                    out.append(r)
                    continue
                r = dict(r)
                r["area_id"] = keep
                key = (keep, r.get("entity_type", ""), r.get("policy_id", ""),
                       r.get("source_id", ""), r.get("region_code", ""), r.get("rel", ""))
                if key in existing:
                    continue  # 已有同样映射，丢弃重复行
                out.append(r)
                existing.add(key)
                changed = True
                moved += 1
            if changed:
                print(f"  {p.name}: 迁移 {sum(1 for r in rows if r.get('area_id')==drop)} 行中的未重复部分")
                if not args.dry_run:
                    write(p, hdr, out)

    # source.area_id 指向 drop 的改为 keep
    for p in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            if r.get("area_id") == drop:
                r["area_id"] = keep
                n += 1
        if n:
            print(f"  {p.name}: source 改挂 {n} 条")
            if not args.dry_run:
                write(p, hdr, rows)

    # 置 drop 为 withdrawn
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        hit = [r for r in rows if r.get("area_id") == drop]
        if not hit:
            continue
        for r in hit:
            print(f"  {p.name}: {drop} {r.get('name')} -> withdrawn（原因：{args.reason or '重复'}）")
            if not args.dry_run:
                r["record_state"] = "withdrawn"
                r["status"] = "已撤销"
                r["updated_at"] = today
        if not args.dry_run:
            write(p, hdr, rows)

    print(f"迁移映射 {moved} 行" + ("（dry-run）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
