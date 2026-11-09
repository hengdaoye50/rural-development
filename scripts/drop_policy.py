"""剔除一条误入 policy 的记录（口径不符 / 层级不符），并归档其 raw 证据。

用途：政策层只收「具体到县区一级对片区化的具体部署」。中央/省级的普适性文件
（如全会规划建议原文）即使全文可得，也不属于本库口径；发现后应剔除而不是留着凑数。

做法：
  1. 从 data/clean/by_province/{ABBR}-policy.csv 删该行
  2. 删掉引用它的 area_policy_map / event 行
  3. raw 存档**移到 archive/{YYYY-MM}/dropped-policy/**，不删（CLAUDE.md：raw 只追加不覆盖）

不直改 data/clean/*.csv 与 sqlite；删完跑 merge -> build -> validate。

用法：
  python scripts/drop_policy.py P540013 "中央全会规划建议，非县区级片区化部署"
  python scripts/drop_policy.py --dry-run P540013 "…"
"""
from __future__ import annotations

import csv
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"
ROOT_CSV = CLEAN


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
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    pid = args[0]
    why = args[1] if len(args) > 1 else ""

    hit_row = None
    hit_file = None
    for p in sorted(BY_PROV.glob("*-policy.csv")):
        header, rows = _read(p)
        keep = [r for r in rows if r.get("policy_id") != pid]
        if len(keep) != len(rows):
            hit_row = next(r for r in rows if r.get("policy_id") == pid)
            hit_file = (p, header, keep, len(rows) - len(keep))
            break
    if not hit_row:
        print(f"找不到 policy {pid}（查 {BY_PROV}/*-policy.csv）")
        return 1

    print(f"剔除 {pid}  {hit_row.get('title', '')[:60]}")
    print(f"  依据：{why}")
    print(f"  url：{hit_row.get('url', '')}")

    for name in ("area_policy_map", "event"):
        for p in sorted(BY_PROV.glob(f"*-{name}.csv")):
            header, rows = _read(p)
            key = "policy_id"
            keep = [r for r in rows if r.get(key) != pid]
            if len(keep) != len(rows):
                print(f"  - {p.name}: 删 {len(rows) - len(keep)} 行（{name}）")
                if not dry:
                    _write(p, header, keep)

    p, header, keep, n = hit_file
    print(f"  - {p.name}: 删 {n} 行（policy）")
    if not dry:
        _write(p, header, keep)

    local = (hit_row.get("local_path") or "").strip()
    if local:
        src = (ROOT / local).parent
        if src.exists():
            dst = ROOT / "archive" / date.today().strftime("%Y-%m") / "dropped-policy" / f"{pid}-{src.name}"
            print(f"  raw 存档移到 {dst.relative_to(ROOT)}")
            if not dry:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.move(str(src), str(dst))
        else:
            print(f"  raw 存档不存在，跳过：{local}")

    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    else:
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
