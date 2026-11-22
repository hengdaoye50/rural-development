# -*- coding: utf-8 -*-
"""迁移 area→belt 后，把悬挂引用改指 belt（幂等，先 --dry-run）。

背景：`migrate_belt_from_area.py` 把「带/廊/圈/线」从 area 迁到 belt 后，
`event` 与 `source` 里仍指向旧 `area_id`。按 `docs/02` 的来源约定，belt 的
`source.area_id` 填 `belt_id`；`event` 同理改 `area_id` 并把 `entity_type` 置 `belt`。

映射来源：
  1. `belt.institutional_note` 里的「由 area Axxxxxx 迁入」；
  2. 三条「同名 belt 已存在、area 被跳过」的历史映射（硬编码，来源见 note）。

用法：
  python scripts/repair_after_belt_migration.py --dry-run
  python scripts/repair_after_belt_migration.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)

# 迁移时因「同名 belt 已存在」跳过、但 area 行被误删的 3 条（2026-11-21 修复记录）
SKIPPED = {
    "A420004": "B420003",   # 黄陂区木兰故里觅乡愁样板带
    "A210026": "B210020",   # 阜蒙县太平沟村—艾友营子村乡村振兴示范带
    "A320081": "B320010",   # 新洋港沿线绿色廊道片区
}


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


def build_map() -> dict[str, str]:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    m = {}
    for bid, note in con.execute("select belt_id, institutional_note from belt"):
        hit = re.search(r"由 area (A\d+) 迁入", note or "")
        if hit:
            m[hit.group(1)] = bid
    m.update(SKIPPED)
    con.close()
    return m


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    amap = build_map()
    print(f"映射 {len(amap)} 条（含 3 条历史跳过）")
    fixed_ev = fixed_src = 0
    for p in sorted(BP.glob("*-event.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            aid = r.get("area_id") or ""
            if aid in amap:
                r["area_id"] = amap[aid]
                r["entity_type"] = "belt"
                n += 1
        if n:
            fixed_ev += n
            print(f"  {p.name}: event {n}")
            if not dry:
                write(p, hdr, rows)
    for p in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(p)
        n = 0
        for r in rows:
            aid = r.get("area_id") or ""
            if aid in amap:
                r["area_id"] = amap[aid]
                n += 1
        if n:
            fixed_src += n
            print(f"  {p.name}: source {n}")
            if not dry:
                write(p, hdr, rows)
    print(f"共改 event {fixed_ev} / source {fixed_src}" + ("（dry-run）" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
