"""一次性修复：恢复被 merge_by_province.py 误删的 56 条 area_source_map 行。

背景：2026-11 收紧 merge 规则时误把「by_province 覆盖到的实体→丢弃 master 多余行」
应用到 area_source_map，导致仅存在于 master 的来源映射被清掉。规则已改回只作用于
region_map，此脚本把 HEAD 版本中缺失的键补回 master。

用法：python scripts/legacy/restore_area_source_map.py
"""
from __future__ import annotations

import csv
import io
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "data" / "clean" / "area_source_map.csv"


def main() -> int:
    blob = subprocess.run(
        ["git", "show", "HEAD:data/clean/area_source_map.csv"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8-sig")
    head = list(csv.DictReader(io.StringIO(blob)))
    with TARGET.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames or [])
        cur = list(reader)
    keys = {(r["area_id"], r["source_id"]) for r in cur}
    added = [r for r in head if (r["area_id"], r["source_id"]) not in keys]
    if not added:
        print("无缺失，跳过")
        return 0
    with TARGET.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(cur + added)
    print(f"补回 {len(added)} 行 -> {len(cur) + len(added)} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
