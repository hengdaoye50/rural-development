"""补齐 `area_region_map`：每个 active 的 area 至少要有 1 条区划归属行。

背景（2026-11-18 接手审校发现）：浙江 13 条 active 片区（A330083–A330095）在
`data/clean/by_province/ZJ-area.csv` 里有记录，但 `ZJ-area_region_map.csv` 里
没有对应行。后果不是报错而是**静默少算**：任何按 `area_region_map` 聚合的
县覆盖、分市统计都会漏掉它们；而按 `area.county_code` 聚合的脚本又数得到，
于是同一库里出现多套县覆盖数字。

判据：`area.county_code` 是片区主体所在县级码（数据字典 §area）。缺失行按
`role='county', is_core=1` 补齐，与 `ingest_area_roster.py` 的写法一致
（`is_core` 目前不参与任何聚合，仅作核心单元标记）。

约束：
  - 只补不收：不删已有行、不改已有行的 role/is_core
  - county_code 为空的跳过并报出（空码是上游问题，不在这里猜）
  - county_code 不是县级码的跳过并报出（市码占位属口径问题，须人工裁定）

用法：
  python scripts/repair_area_region_map.py --dry-run
  python scripts/repair_area_region_map.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
DB = ROOT / "data" / "db" / "片区库.sqlite3"

MAP_FIELDS = ["area_id", "region_code", "role", "is_core"]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def main() -> int:
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    county_level = {
        r["region_code"] for r in con.execute("select region_code from region where level='county'")
    }

    touched = 0
    skipped: list[str] = []
    for area_csv in sorted(BY_PROV.glob("*-area.csv")):
        abbr = area_csv.name[: -len("-area.csv")]
        map_csv = BY_PROV / f"{abbr}-area_region_map.csv"
        _, areas = _read(area_csv)
        header, maps = _read(map_csv)
        if not header:
            header = list(MAP_FIELDS)
        have = {r.get("area_id") for r in maps}
        adds = []
        for a in areas:
            aid = a.get("area_id") or ""
            if not aid or a.get("record_state") != "active" or aid in have:
                continue
            cc = (a.get("county_code") or "").strip()
            if not cc:
                skipped.append(f"{aid} {a.get('name','')}：county_code 为空")
                continue
            if cc not in county_level:
                skipped.append(f"{aid} {a.get('name','')}：county_code={cc} 不是县级码")
                continue
            adds.append({"area_id": aid, "region_code": cc, "role": "county", "is_core": "1"})
        if not adds:
            continue
        print(f"{abbr}: 补 {len(adds)} 行 -> {map_csv.name}")
        for r in adds:
            print(f"  + {r['area_id']} -> {r['region_code']}")
        touched += len(adds)
        if not dry:
            _write(map_csv, header if set(MAP_FIELDS) <= set(header) else list(MAP_FIELDS),
                   maps + adds)

    print(f"\n合计补 {touched} 行" + ("（dry-run，未写盘）" if dry else ""))
    if skipped:
        print(f"跳过 {len(skipped)} 条，需人工处理：")
        for s in skipped:
            print("  -", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
