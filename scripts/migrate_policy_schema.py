"""把 policy / event CSV 表头升级到 v0.2 政策层结构（幂等）。

禁止手改 data/clean；本脚本是唯一入口。
按列名保留旧数据：旧列照抄，新列留空（event.entity_type 默认 area）。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"

POLICY_COLS = [
    "policy_id", "title", "doc_no", "issuer", "issuer_level",
    "issued_ymd", "published_ymd", "date_precision", "doc_type",
    "source_kind", "province_code", "city_code", "county_code",
    "instruments", "scope_desc", "target_areas", "budget_wan",
    "valid_state", "url", "local_path", "hash_sha256", "full_text_chars",
    "summary", "credibility", "fetched_at", "record_state",
    "created_at", "updated_at", "created_by",
]

EVENT_COLS = [
    "event_id", "area_id", "entity_type", "event_type", "ymd",
    "note", "source_id", "policy_id",
]

AREA_POLICY_MAP_COLS = ["area_id", "policy_id", "entity_type", "rel"]

# 新列缺省值
DEFAULTS = {
    "policy": {
        "date_precision": "unknown",
        "source_kind": "政策文件",
        "valid_state": "未知",
    },
    "event": {"entity_type": "area"},
    "area_policy_map": {"entity_type": "area", "rel": "support"},
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), list(rd)


def _write(path: Path, cols: list[str], rows: list[dict[str, str]], table: str) -> bool:
    changed = False
    if not path.exists():
        out = []
        for r in rows:
            out.append({c: r.get(c, DEFAULTS.get(table, {}).get(c, "")) or "" for c in cols})
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(out)
        return True

    old_cols, rows = _read(path)
    if old_cols == cols:
        return False

    out = []
    for r in rows:
        row = {}
        for c in cols:
            v = r.get(c)
            if v in (None, ""):
                v = DEFAULTS.get(table, {}).get(c, "")
            row[c] = v or ""
        out.append(row)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    changed = True
    return changed


def migrate() -> int:
    jobs = [
        ("policy", POLICY_COLS),
        ("event", EVENT_COLS),
    ]
    touched = 0

    for table, cols in jobs:
        master = CLEAN / f"{table}.csv"
        if _write(master, cols, [], table):
            print(f"upgraded master: {master.name}")
            touched += 1
        for p in sorted(BY_PROV.glob(f"*-{table}.csv")):
            if _write(p, cols, [], table):
                print(f"upgraded by_province: {p.name}")
                touched += 1

    map_path = CLEAN / "area_policy_map.csv"
    if not map_path.exists():
        _write(map_path, AREA_POLICY_MAP_COLS, [], "area_policy_map")
        print("created: area_policy_map.csv")
        touched += 1

    print(f"OK: {touched} file(s) changed")
    return 0


if __name__ == "__main__":
    sys.exit(migrate())
