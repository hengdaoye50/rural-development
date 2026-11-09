"""补录一条 area_policy_map 关联（片区 ↔ 政策）。

用途：采集端在 JSONL 的 `areas` 里漏挂某个片区时，`ingest_policy.py` 的 url 去重
会整条跳过，导致这条映射补不进去。此脚本按 area_id + policy_id 定点追加一行。

只写 data/clean/by_province/{ABBR}-area_policy_map.csv，再由 merge_by_province.py
覆盖根表——不直接改 data/clean/*.csv 与 sqlite（CLAUDE.md 结构红线）。

用法：
  python scripts/add_area_policy_link.py A120007 P120001 primary "市级方案点名「古蕴田园乡村旅游」示范片区"
  python scripts/add_area_policy_link.py --dry-run A210009 P210001 primary "省级名单含桓仁雅河带"
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"

PROV_ABBR = {
    "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
    "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
    "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
    "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
    "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
    "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
    "650000": "XJ",
}
REL_VALUES = ("primary", "support", "mention")
COLS = ["area_id", "policy_id", "entity_type", "rel"]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) < 3:
        print(__doc__)
        return 2
    area_id, policy_id, rel = args[0], args[1], args[2]
    why = args[3] if len(args) > 3 else ""
    if rel not in REL_VALUES:
        print(f"rel={rel!r} 不在 {REL_VALUES} 内")
        return 2

    # 政策省份：从 by_province 的 policy CSV 反查（比读根表快且不受合并状态影响）
    prov, found_in = "", ""
    for p in sorted(BY_PROV.glob("*-policy.csv")):
        abbr = p.name.split("-")[0]
        for r in _read(p)[1]:
            if r.get("policy_id") == policy_id:
                prov, found_in = abbr, p.name
                break
        if prov:
            break
    if not prov:
        print(f"找不到 policy {policy_id}（查 {BY_PROV}/*-policy.csv）")
        return 1

    map_path = BY_PROV / f"{prov}-area_policy_map.csv"
    header, rows = _read(map_path)
    header = header or COLS

    # 片区必须已在 area 表里，防止 id 幻觉
    area_abbr = ""
    for p in sorted(BY_PROV.glob("*-area.csv")):
        if any(r.get("area_id") == area_id for r in _read(p)[1]):
            area_abbr = p.name.split("-")[0]
            break
    if not area_abbr:
        print(f"area_id {area_id} 不在 by_province 任何 area CSV 内，拒绝写入")
        return 1

    if any(r.get("area_id") == area_id and r.get("policy_id") == policy_id for r in rows):
        print(f"已存在：{area_id} ↔ {policy_id}，无需重复")
        return 0

    rows.append({
        "area_id": area_id,
        "policy_id": policy_id,
        "entity_type": "area",
        "rel": rel,
    })
    print(f"  + {prov} :: {area_id} ↔ {policy_id} ({rel})  {why}")
    print(f"    政策来自 {found_in}，片区属 {area_abbr}，写入 {map_path.name}")
    if not dry:
        _write(map_path, header, rows)
        print("接着跑：merge_by_province -> build_db -> validate_db")
    else:
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
