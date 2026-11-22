# -*- coding: utf-8 -*-
"""按裁定表下架记录（幂等，先 --dry-run）。

读 `data/stage/candidates/*-decisions-*.csv`，把「建议」列命中指定取值的记录
置 `record_state='withdrawn'`（不删数据、不动 raw）。

用法：
  python scripts/withdraw_by_decision.py --file data/stage/candidates/brand-name-decisions-2026-11-21.csv --actions 拆分
  python scripts/withdraw_by_decision.py --file ... --actions 拆分,drop --dry-run
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
    ap.add_argument("--file", required=True)
    ap.add_argument("--actions", default="拆分", help="建议列的取值，逗号分隔")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    acts = {x.strip() for x in args.actions.split(",") if x.strip()}
    _, rows = read(Path(args.file))
    ids = {r["area_id"] for r in rows if (r.get("建议") or "").strip() in acts}
    print(f"裁定表 {Path(args.file).name}｜动作 {sorted(acts)}｜命中 {len(ids)} 条")
    for r in rows:
        if r["area_id"] in ids:
            print(f"  {r['area_id']} {r['name'][:32]}｜{r.get('理由','')[:40]}")

    today = date.today().isoformat()
    changed = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, arows = read(p)
        hit = [r for r in arows if r.get("area_id") in ids and r.get("record_state") == "active"]
        if not hit:
            continue
        changed += len(hit)
        print(f"  {p.name}: {len(hit)}")
        if args.dry_run:
            continue
        for r in hit:
            r["record_state"] = "withdrawn"
            r["status"] = "已撤销"
            r["updated_at"] = today
        write(p, hdr, arows)
    print(f"共下架 {changed} 条" + ("（dry-run 未写盘）" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
