"""项目结构规整：把散乱产物收敛到 CLAUDE.md 约定的结构。

幂等，可重复执行。只移动与改名，不删除任何文件。
所有被移动文件的引用路径（CSV 里的 local_path）同步改写。

用法：
  python scripts/migrate_layout.py --dry-run
  python scripts/migrate_layout.py
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
STAGE = DATA / "stage"
CLEAN = DATA / "clean"
BY_PROV = CLEAN / "by_province"
SCRIPTS = ROOT / "scripts"
ARCHIVE = ROOT / "archive" / "2026-10" / "layout"

# 一次性批次脚本与调试脚本（不参与管线）
LEGACY = [
    "js_batch01_emit.py", "zj_batch03_emit.py", "zj_batch05_append.py",
    "sd_batch02.py", "sd_batch04.py", "sd_batch08_jn_wf.py", "_xz_batch01.py",
    "fold_zj_batch.py", "fix_batch03_align.py", "fix_js_batch02.py", "fix_source_belt.py",
    "_acceptance_stats.py", "_check2.py", "_check_links.py", "_cmp_master_by.py",
    "_debug_snap.py", "_diag_fk.py", "_diag_fk2.py", "_inspect_debt.py", "_list_jszjsd.py",
    "_pilot_build_jsonl.py", "_spot_dates.py", "_stats2.py", "_stats_bulletin.py",
    "_survey_debt.py",
]

# raw 顶层两套命名：6位码/中文 → 2字母省码
RAW_RENAMES = {"330000-浙江": "ZJ", "310000": "SH"}
# 零引用孤儿目录 → 归档
RAW_ORPHANS = ["310000", "other"]

TABLE_NAMES = {
    "area", "belt", "source", "event", "policy",
    "area_region_map", "belt_region_map", "area_source_map", "area_policy_map",
}

dry = "--dry-run" in sys.argv
actions: list[str] = []


def log(msg: str) -> None:
    actions.append(msg)
    print(("  [dry] " if dry else "  ") + msg)


def move(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        raise SystemExit(f"目标已存在，停止：{dst}")
    log(f"move {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def merge_dir(src: Path, dst: Path) -> None:
    """把 src 下的子项并入 dst（dst 已存在）。"""
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        target = dst / item.name
        if target.exists():
            raise SystemExit(f"合并冲突，停止：{target}")
        log(f"merge {item.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        if not dry:
            shutil.move(str(item), str(target))
    if not dry and not any(src.iterdir()):
        src.rmdir()


# ---------- 1. data/stage 分层 ----------
def step_stage() -> None:
    print("[1] data/stage 分层")
    sub = {"batches": STAGE / "batches", "candidates": STAGE / "candidates"}
    for name, d in sub.items():
        if not dry:
            d.mkdir(parents=True, exist_ok=True)
    for f in sorted(STAGE.glob("POL-*.jsonl")):
        move(f, sub["batches"] / f.name)
    for f in sorted(STAGE.glob("*-candidates.csv")):
        move(f, sub["candidates"] / f.name)
    # shards 已在子目录；空的 pilot 归档
    pilot = STAGE / "pilot"
    if pilot.exists() and not any(pilot.iterdir()):
        log(f"rmdir 空目录 {pilot.relative_to(ROOT)}")
        if not dry:
            pilot.rmdir()


# ---------- 2. data/raw 命名统一 ----------
def step_raw() -> None:
    print("[2] data/raw 命名统一")
    for old, new in RAW_RENAMES.items():
        src, dst = RAW / old, RAW / new
        if not src.exists():
            continue
        if dst.exists():
            merge_dir(src, dst)
        else:
            move(src, dst)
    for orphan in RAW_ORPHANS:
        p = RAW / orphan
        if p.exists():
            move(p, ARCHIVE / "raw" / orphan)


# ---------- 3. clean/by_province 命名规整 ----------
def step_by_province() -> None:
    print("[3] data/clean/by_province 命名规整")
    for f in sorted(BY_PROV.glob("*.csv")):
        parts = f.stem.split("-")
        if len(parts) == 2 and parts[1] in TABLE_NAMES:
            continue
        move(f, ARCHIVE / "by_province" / f.name)


# ---------- 4. scripts 归档 legacy ----------
def step_scripts() -> None:
    print("[4] scripts/legacy 归档")
    legacy_dir = SCRIPTS / "legacy"
    for name in LEGACY:
        f = SCRIPTS / name
        if f.exists():
            move(f, legacy_dir / name)


# ---------- 5. 改写 CSV 中的 local_path ----------
def step_rewrite_paths() -> None:
    print("[5] 改写 CSV 中的 raw 路径引用")
    mapping = {f"data/raw/{old}/": f"data/raw/{new}/" for old, new in RAW_RENAMES.items()}
    if not mapping:
        return
    targets = list(CLEAN.glob("*.csv")) + list(BY_PROV.glob("*.csv"))
    for p in targets:
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            rd = csv.DictReader(f)
            header = list(rd.fieldnames or [])
            rows = [r for r in rd if any(r.values())]
        if "local_path" not in header:
            continue
        n = 0
        for r in rows:
            lp = r.get("local_path") or ""
            for old, new in mapping.items():
                if old in lp:
                    r["local_path"] = lp.replace(old, new)
                    n += 1
                    break
        if n:
            log(f"改写 {n} 条 local_path: {p.name}")
            if not dry:
                with p.open("w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                    w.writeheader()
                    for r in rows:
                        w.writerow({h: r.get(h, "") or "" for h in header})


def main() -> int:
    step_stage()
    step_raw()
    step_by_province()
    step_scripts()
    step_rewrite_paths()

    print(f"\n{'[dry-run] ' if dry else ''}共 {len(actions)} 项操作")
    if dry:
        print("未落盘。去掉 --dry-run 执行。")
    else:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
