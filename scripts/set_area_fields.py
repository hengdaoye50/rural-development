# -*- coding: utf-8 -*-
"""按 area_id 修改字段（幂等，先 --dry-run）。支持成立时间/精度/名称/状态。

用法：
  python scripts/set_area_fields.py --id A350002 --founded 2021 --precision year --dry-run
  python scripts/set_area_fields.py --id A350002 --founded 2021 --precision year
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
    ap.add_argument("--id", required=True)
    ap.add_argument("--founded", help="成立时间，如 2021 或 2021-05-01")
    ap.add_argument("--precision", choices=["day", "month", "year", "unknown"])
    ap.add_argument("--status", choices=["运行中", "待核", "已完成", "已撤销"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    today = date.today().isoformat()
    done = False
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        hits = [r for r in rows if r.get("area_id") == args.id]
        if not hits:
            continue
        for r in hits:
            print(f"{args.id} {r.get('name')}")
            if args.founded:
                print(f"  founded_ymd: {r.get('founded_ymd')} -> {args.founded}")
                r["founded_ymd"] = args.founded
            if args.precision:
                print(f"  founded_precision: {r.get('founded_precision')} -> {args.precision}")
                r["founded_precision"] = args.precision
            if args.status:
                print(f"  status: {r.get('status')} -> {args.status}")
                r["status"] = args.status
            r["updated_at"] = today
        done = True
        if not args.dry_run:
            write(p, hdr, rows)
        break
    if not done:
        print("找不到", args.id)
        return 1
    print("dry-run 未写盘" if args.dry_run else "已写盘")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
