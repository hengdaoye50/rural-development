"""Fold ZJ-*-batch0N.csv into ZJ-<table>.csv (keyed, by_province 优先)."""
from __future__ import annotations

import csv
import re
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
KEYS = {
    "area": "area_id",
    "source": "source_id",
    "area_region_map": ("area_id", "region_code", "role"),
    "area_source_map": ("area_id", "source_id"),
    "belt": "belt_id",
    "belt_region_map": ("belt_id", "region_code", "role"),
}


def read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if any((v or "") for v in r.values())]


def write(p: Path, fields: list[str], rows: list[dict]) -> None:
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({h: (r.get(h) or "") for h in fields})


def fold_one(table: str) -> int:
    main = BY / f"ZJ-{table}.csv"
    extras = sorted(BY.glob(f"ZJ-{table}-batch*.csv")) + sorted(
        BY.glob(f"ZJ-{table}_batch*.csv")
    )
    if not extras:
        return 0
    rows = read(main)
    if not rows:
        # take header from first extra
        for e in extras:
            er = read(e)
            if er:
                rows = er
                break
        fields = list(rows[0].keys()) if rows else []
    else:
        fields = list(rows[0].keys())
    key = KEYS.get(table)
    index = {}
    for r in rows:
        k = tuple(r.get(x, "") for x in key) if isinstance(key, tuple) else r.get(key, "")
        index[k] = r
    before = len(index)
    for e in extras:
        for r in read(e):
            k = tuple(r.get(x, "") for x in key) if isinstance(key, tuple) else r.get(key, "")
            if k not in index or not index[k]:
                index[k] = r
            # extras win if same key? prefer extras as newer
            else:
                merged = dict(index[k])
                merged.update({h: (v or "") for h, v in r.items() if v})
                index[k] = merged
    write(main, fields, list(index.values()))
    print(f"ZJ-{table}: {before} -> {len(index)} (+{len(index)-before})")
    return len(index) - before


if __name__ == "__main__":
    total = 0
    for t in KEYS:
        total += fold_one(t)
    print("folded delta", total)
