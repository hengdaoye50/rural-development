"""执行 reports/qa/area-fix-proposal.md 中经人工确认的区划归属修正。

改动只写 data/clean/by_province/{ABBR}-{area,area_region_map}.csv，
再由 merge_by_province.py 覆盖根表——不直接改 data/clean/*.csv 与 sqlite。

每条 fix 自带 old → new，只有当前值仍等于 old 时才改，可反复重跑。
用法：
  python scripts/apply_area_fixes.py            # 执行
  python scripts/apply_area_fixes.py --dry-run  # 只看会改哪些行
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"

# area_id, 省缩写, 现 county_code, 应 county_code, 依据
FIXES: list[tuple[str, str, str, str, str]] = [
    ("A320077", "JS", "320114", "320117",
     "cover_desc 自述「溧水区无想山南麓」，320114 为雨花台区"),
    ("A360010", "JX", "360782", "360727",
     "360782 是 region 表里的占位码（name 等于代码本身），龙南市实为 360727"),
    ("A360019", "JX", "360727", "360726",
     "360727 被龙南占用后腾出的错位；安远县实为 360726"),
    ("A510016", "SC", "510681", "510682",
     "issuer 与 cover_desc 均指什邡市，510681 是广汉市；什邡为 510682"),
]


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        return list(rows[0].keys()) if rows else [], rows


def _write(path: Path, cols: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    dry = "--dry-run" in sys.argv
    changed = 0
    for area_id, abbr, old, new, why in FIXES:
        for table, col in (("area", "county_code"), ("area_region_map", "region_code")):
            path = BY_PROV / f"{abbr}-{table}.csv"
            cols, rows = _read(path)
            hit = [r for r in rows if r.get("area_id") == area_id and r.get(col) == old]
            if not hit:
                stale = [r.get(col) for r in rows if r.get("area_id") == area_id]
                print(f"  跳过 {area_id} {table}: 无 {old} 行（现值 {stale}）")
                continue
            for r in hit:
                r[col] = new
            changed += len(hit)
            print(f"  {area_id} {table}: {old} -> {new}  ({why})")
            if not dry:
                _write(path, cols, rows)
    print(f"{'dry-run，' if dry else ''}共改 {changed} 行")
    if not dry and changed:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
