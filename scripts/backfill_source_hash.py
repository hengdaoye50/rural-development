"""为 source 快照补录 hash_sha256。

只填空值，不改已有非空哈希；不符的单独报出供复核。

用法：
  python scripts/backfill_source_hash.py --dry-run
  python scripts/backfill_source_hash.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BY_PROV = ROOT / "data" / "clean" / "by_province"


def resolve_file(local_path: str) -> Path | None:
    p = Path(local_path)
    if p.is_dir():
        for name in ("原文.md", "原件.pdf", "原件.html"):
            if (p / name).exists():
                return p / name
        files = sorted(p.glob("*"))
        return files[0] if files else None
    return p if p.exists() else None


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") or "" for h in header})


def main() -> int:
    dry = "--dry-run" in sys.argv
    fix_mismatch = "--fix-mismatch" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute("select source_id, local_path, hash_sha256 from source"))

    need: dict[str, str] = {}
    mismatch: list[tuple[str, str]] = []
    missing_file: list[str] = []
    for r in rows:
        lp = r["local_path"]
        if not lp:
            continue
        f = resolve_file(lp)
        if f is None:
            missing_file.append(r["source_id"])
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if not r["hash_sha256"]:
            need[r["source_id"]] = h
        elif r["hash_sha256"] != h:
            mismatch.append((r["source_id"], h))
            if fix_mismatch:
                need[r["source_id"]] = h

    print(f"待补哈希 {len(need)} 条；已有哈希不符 {len(mismatch)} 条；文件缺失 {len(missing_file)} 条")
    if mismatch and not fix_mismatch:
        print("  哈希不符（未改动，确认文件内容无损后加 --fix-mismatch 重算）:",
              [s for s, _ in mismatch][:10])

    if not dry and need:
        touched = 0
        for p in sorted(BY_PROV.glob("*-source.csv")):
            header, rows_ = _read(p)
            if not header:
                continue
            n = 0
            for r in rows_:
                sid = r.get("source_id")
                if sid not in need:
                    continue
                if not r.get("hash_sha256") or fix_mismatch:
                    r["hash_sha256"] = need[sid]
                    n += 1
            if n:
                _write(p, header, rows_)
                touched += n
        print(f"已补录 {touched} 条")
        print("接着跑：merge_by_province -> build_db")
    elif dry:
        print("未落盘。去掉 --dry-run 执行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
