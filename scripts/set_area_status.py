# -*- coding: utf-8 -*-
"""按 area_id 批量设置 status（幂等，先 --dry-run）。

用途：待核 ↔ 运行中 的人工裁定落地。只写 `data/clean/by_province/*-area.csv`，
不碰 master（merge 会重建）。

用法：
  python scripts/set_area_status.py --ids A330003,A330010,A330016 --status 运行中 --dry-run
  python scripts/set_area_status.py --ids A330003,A330010,A330016 --status 运行中
跑完接 merge_by_province -> build_db -> validate_db -> health_report
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
VALID = {"运行中", "待核", "已完成", "已撤销"}


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
    ap.add_argument("--ids", required=True, help="逗号分隔的 area_id")
    ap.add_argument("--status", required=True, choices=sorted(VALID))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ids = {x.strip() for x in args.ids.split(",") if x.strip()}
    print(f"目标 {len(ids)} 条 → {args.status}")

    today = date.today().isoformat()
    changed = 0
    found: set[str] = set()
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        hit = [r for r in rows if r.get("area_id") in ids]
        if not hit:
            continue
        for r in hit:
            found.add(r["area_id"])
            print(f"  {r['area_id']} {r.get('name','')}｜{r.get('status','')} → {args.status}")
            if not args.dry_run:
                r["status"] = args.status
                r["updated_at"] = today
        changed += len(hit)
        if not args.dry_run:
            write(p, hdr, rows)
    missing = ids - found
    if missing:
        print("  未找到：", ", ".join(sorted(missing)))
    print(f"共改 {changed} 条" + ("（dry-run 未写盘）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
