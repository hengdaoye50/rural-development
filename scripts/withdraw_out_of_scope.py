# -*- coding: utf-8 -*-
"""按口径审计清单下架「明确不是片区」的记录（幂等，先 --dry-run）。

只处理 `reports/qa/口径外候选-*.csv` 里 `rec=drop` 的行（田园综合体、示范村群落、
小镇/项目、规划分区）。处理方式：`area.record_state='withdrawn'`——
**不删数据、不动 raw**，视图与统计自动排除，符合「口径变更不改数据」的既有裁定。

用法：
  python scripts/withdraw_out_of_scope.py --dry-run
  python scripts/withdraw_out_of_scope.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
QA = ROOT / "reports" / "qa"


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
    files = sorted(QA.glob("口径外候选-*.csv"))
    if not files:
        print("找不到审计清单，先跑 scripts/audit_scope.py")
        return 1
    _, rows = read(files[-1])
    drops = [r for r in rows if r.get("rec") == "drop"]
    ids = {r["area_id"] for r in drops}
    print(f"清单 {files[-1].name}：drop {len(drops)} 条")

    changed = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, arows = read(p)
        hit = [r for r in arows if r.get("area_id") in ids]
        if not hit:
            continue
        changed += len(hit)
        print(f"  {p.name}: 下架 {len(hit)} 条")
        if dry:
            continue
        for r in hit:
            r["record_state"] = "withdrawn"
            r["status"] = "已撤销"
            r["updated_at"] = date.today().isoformat()
        write(p, hdr, arows)
    print(f"共下架 {changed} 条" + ("（dry-run 未写盘）" if dry else ""))
    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db -> health_report -> check_doc_caliber --fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
