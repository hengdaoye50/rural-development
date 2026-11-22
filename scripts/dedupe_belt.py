# -*- coding: utf-8 -*-
"""belt 去重：同一省 + 同 name_norm + 同 belt_type 只留一条（幂等，先 --dry-run）。

场景：`migrate_belt_from_area.py` 把 area 里的「样板带」迁入 belt 时，
湖北等省原本已有同名 belt（20 条样板带），产生重复。保留**原有** belt（非迁移标记），
把重复行删除，并把其 `source` / `event` / 区划行改指保留的那条。

用法：
  python scripts/dedupe_belt.py --dry-run
  python scripts/dedupe_belt.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
MIG = "migrate-belt-from-area"


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
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in con.execute("""select belt_id, name, name_norm, belt_type, province_code, created_by
                            from belt where record_state='active'"""):
        groups[(r["province_code"], (r["name_norm"] or "").strip(), r["belt_type"])].append(dict(r))
    con.close()

    dup = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"重复组 {len(dup)}｜涉及 {sum(len(v) for v in dup.values())} 条")
    drop: set[str] = set()
    keep_of: dict[str, str] = {}
    for k, v in dup.items():
        v.sort(key=lambda x: (x["created_by"] == MIG, x["belt_id"]))  # 原记录优先
        keep, rest = v[0]["belt_id"], [x["belt_id"] for x in v[1:]]
        for d in rest:
            drop.add(d)
            keep_of[d] = keep
        print(f"  留 {keep}｜删 {rest}｜{k[1][:26]}")
    if not drop:
        return 0
    if dry:
        print("dry-run，未写盘")
        return 0

    for p in sorted(BP.glob("*-belt.csv")):
        hdr, rows = read(p)
        n = sum(1 for r in rows if r.get("belt_id") in drop)
        if n:
            write(p, hdr, [r for r in rows if r.get("belt_id") not in drop])
            print(f"  {p.name}: 删 {n}")
    for p in sorted(BP.glob("*-belt_region_map.csv")):
        hdr, rows = read(p)
        out, seen = [], set()
        n = 0
        for r in rows:
            bid = r.get("belt_id") or ""
            if bid in drop:
                n += 1
                r = {**r, "belt_id": keep_of[bid]}
                bid = r["belt_id"]
            key = (bid, r.get("region_code"), r.get("role"))
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        if n or len(out) != len(rows):
            write(p, hdr, out)
            print(f"  {p.name}: 改指 {n} 行")
    for p in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            if r.get("area_id") in keep_of:
                r["area_id"] = keep_of[r["area_id"]]
                n += 1
        if n:
            write(p, hdr, rows)
            print(f"  {p.name}: source {n}")
    for p in sorted(BP.glob("*-event.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            if r.get("area_id") in keep_of:
                r["area_id"] = keep_of[r["area_id"]]
                n += 1
        if n:
            write(p, hdr, rows)
            print(f"  {p.name}: event {n}")
    print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
