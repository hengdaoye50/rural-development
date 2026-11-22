# -*- coding: utf-8 -*-
"""状态与证据对齐：`运行中` 但无 primary/support 的片区改回 `待核`（幂等，先 --dry-run）。

口径：`待核` = 证据链不达标（`docs/01` §10）。一条记录若没有任何 primary/support
政策挂接，它就不该显示为运行中——否则 E 组里混着「运行中」，对外报数会自相矛盾。

只写 `data/clean/by_province/*-area.csv`（area 是实体表，merge 会重建 master）。

用法：
  python scripts/fix_status_evidence.py --dry-run
  python scripts/fix_status_evidence.py
跑完接 merge_by_province -> build_db -> validate_db -> health_report
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
    rows = [dict(r) for r in con.execute("""
        select a.area_id, a.name, a.province_code from area a
        where a.record_state='active' and a.status='运行中'
          and not exists (select 1 from area_policy_map m
                          where m.area_id=a.area_id and m.rel in ('primary','support'))
        order by a.area_id""")]
    con.close()
    ids = {r["area_id"] for r in rows}
    print(f"运行中但无 primary/support：{len(rows)} 条")
    for r in rows[:8]:
        print(f"  {r['area_id']} {r['name'][:34]}")

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
            r["status"] = "待核"
            r["updated_at"] = today
        write(p, hdr, arows)
    print(f"共改 {changed} 条" + ("（dry-run 未写盘）" if dry else ""))
    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db -> health_report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
