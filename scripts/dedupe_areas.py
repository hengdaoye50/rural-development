"""Resolve active duplicate name_norm+county and unsourced areas."""
from __future__ import annotations

import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
ROOT = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean")


def load(p: Path) -> tuple[list[dict], list[str]]:
    if not p.exists():
        return [], []
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
    fields = list(rows[0].keys()) if rows else []
    return rows, fields


def save(p: Path, fields: list[str], rows: list[dict]) -> None:
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({h: (r.get(h) or "") for h in fields})


def main() -> None:
    # collect all area rows with provenance
    all_rows: list[tuple[str, dict]] = []
    for p in sorted(BY.glob("*-area.csv")):
        rows, _ = load(p)
        for r in rows:
            all_rows.append((p.name, r))

    # source linkage
    src_area = set()
    for p in sorted(BY.glob("*-area_source_map.csv")):
        rows, _ = load(p)
        for r in rows:
            if r.get("entity_type") in ("", "area") or r.get("entity_type") is None:
                src_area.add(r.get("area_id"))
            elif r.get("entity_type") == "area":
                src_area.add(r.get("area_id"))

    # also first_source_id
    for _, r in all_rows:
        if (r.get("first_source_id") or "").startswith("S"):
            src_area.add(r.get("area_id"))

    # duplicates among active
    by_key: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    for fname, r in all_rows:
        if (r.get("record_state") or "active") != "active":
            continue
        key = ((r.get("county_code") or ""), (r.get("name_norm") or r.get("name") or ""))
        by_key.setdefault(key, []).append((fname, r))

    supersede_ids = set()
    for key, items in by_key.items():
        if len(items) <= 1:
            continue
        # prefer one with source, then lower area_id
        def score(item):
            fname, r = item
            has_src = 1 if r.get("area_id") in src_area or (r.get("first_source_id") or "").startswith("S") else 0
            return (has_src, -int((r.get("area_id") or "A999999")[1:] or 0))
        items_sorted = sorted(items, key=score, reverse=True)
        keep = items_sorted[0][1].get("area_id")
        for _, r in items_sorted[1:]:
            supersede_ids.add(r.get("area_id"))
        print("dup", key, "keep", keep, "drop", [r.get("area_id") for _, r in items_sorted[1:]])

    n = 0
    for p in sorted(BY.glob("*-area.csv")):
        rows, fields = load(p)
        if not rows:
            continue
        changed = False
        for r in rows:
            aid = r.get("area_id")
            if aid in supersede_ids:
                r["record_state"] = "superseded"
                r["status"] = "已更名" if r.get("status") == "运行中" else r.get("status")
                # better: keep status but record_state superseded
                r["status"] = "待核"
                r["type_primary_note"] = (r.get("type_primary_note") or "") + "；与同县同名条目重复，保留主条目"
                changed = True
                n += 1
            elif (r.get("record_state") or "active") == "active" and r.get("status") == "运行中":
                if aid not in src_area and not (r.get("first_source_id") or "").startswith("S"):
                    r["status"] = "待核"
                    changed = True
                    n += 1
        if changed:
            save(p, fields, rows)
    print("adjusted", n)


if __name__ == "__main__":
    main()
