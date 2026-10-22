"""把 data/clean/by_province/*-*.csv 合并进 data/clean/*.csv（幂等去重）。

规则：
- by_province 优先（更新）；master 仅补缺
- 实体表（area/belt/source/event/policy）：by_province 为权威集合，master 孤儿键丢弃
- map 表：role 必须合法；指向已删除实体的行丢弃
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"

TABLES = [
    "area", "belt", "source", "event", "policy",
    "area_region_map", "belt_region_map", "area_source_map",
]
KEYS = {
    "area": ["area_id"],
    "belt": ["belt_id"],
    "source": ["source_id"],
    "event": ["event_id"],
    "policy": ["policy_id"],
    "area_region_map": ["area_id", "region_code", "role"],
    "belt_region_map": ["belt_id", "region_code", "role"],
    "area_source_map": ["area_id", "source_id"],
}
# region_map.role 受 build_db CHECK 约束
ROLE_OK = {"county", "town", "village", "spine", "node"}
ENTITY_TABLES = {"area", "belt", "source", "event", "policy"}


def _read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def _by_ids(table: str, id_field: str) -> set[str]:
    out: set[str] = set()
    for p in BY_PROV.glob(f"*-{table}.csv"):
        for r in _read(p):
            v = r.get(id_field)
            if v:
                out.add(v)
    return out


def merge() -> int:
    if not BY_PROV.exists():
        print("no by_province dir")
        return 0

    area_ids = _by_ids("area", "area_id")
    belt_ids = _by_ids("belt", "belt_id")

    for table in TABLES:
        master_path = CLEAN / f"{table}.csv"
        header = None
        if master_path.exists():
            with master_path.open("r", encoding="utf-8-sig", newline="") as f:
                header = csv.DictReader(f).fieldnames
        if not header:
            for p in sorted(BY_PROV.glob(f"*-{table}.csv")):
                rows = _read(p)
                if rows:
                    header = list(rows[0].keys())
                    break
        if not header:
            continue

        index: dict[tuple, dict[str, str]] = {}
        by_keys: set[tuple] = set()
        for p in sorted(BY_PROV.glob(f"*-{table}.csv")):
            for r in _read(p):
                key = tuple(r.get(k, "") for k in KEYS[table])
                if any(r.values()):
                    index[key] = r
                    by_keys.add(key)

        prune_orphans = table in ENTITY_TABLES and bool(by_keys)
        for r in _read(master_path):
            key = tuple(r.get(k, "") for k in KEYS[table])
            if key in index:
                continue
            if table in ("area_region_map", "belt_region_map") and r.get("role") not in ROLE_OK:
                continue
            if prune_orphans and key not in by_keys:
                continue
            index[key] = r

        if table in ("area_region_map", "belt_region_map"):
            index = {k: v for k, v in index.items() if v.get("role") in ROLE_OK}

        # map 外键：不能指向已删除实体
        if table == "area_region_map":
            index = {
                k: v for k, v in index.items() if v.get("area_id") in area_ids
            }
        elif table == "belt_region_map":
            index = {
                k: v for k, v in index.items() if v.get("belt_id") in belt_ids
            }
        elif table == "area_source_map":
            filtered = {}
            for k, v in index.items():
                if v.get("entity_type") == "belt":
                    if v.get("area_id") in belt_ids:
                        filtered[k] = v
                elif v.get("area_id") in area_ids:
                    filtered[k] = v
            index = filtered

        with master_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            w.writeheader()
            for key in sorted(index):
                row = index[key]
                w.writerow({h: row.get(h, "") for h in header})
        print(f"{table}: {len(index)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(merge())
