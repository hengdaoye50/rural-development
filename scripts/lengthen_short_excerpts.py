# -*- coding: utf-8 -*-
"""把过短的 `source.excerpt` 按快照原文向上扩展（幂等，只扩不改字）。

为什么需要：`validate_db` 要求 `excerpt` ≥40 字；名单类 OCR 快照常是「一行一个片区名」，
单行摘录不足 40 字。扩展时只用快照里**连续原文行**，保证 `excerpt in 快照` 仍逐字成立。

用法：
  python scripts/lengthen_short_excerpts.py --dry-run
  python scripts/lengthen_short_excerpts.py           # 就地改 by_province/*-source.csv
改完接：merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
MIN = 40
MAX_BACK = 12


def read(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
    for r in rows:
        assert set(r) <= set(hdr), f"字段超出表头：{set(r) - set(hdr)}"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def expand(text: str, excerpt: str) -> str:
    """在 text 中定位 excerpt 末行，向上取连续行直到 ≥MIN 字。"""
    lines = text.splitlines()
    tail = excerpt.splitlines()[-1].strip()
    if not tail:
        return excerpt
    idx = next((i for i, ln in enumerate(lines) if ln.strip() == tail), None)
    if idx is None:
        return excerpt
    start = idx
    while start > 0 and (idx - start) < MAX_BACK:
        seg = "\n".join(lines[start:idx + 1]).strip()
        if len(seg) >= MIN:
            return seg
        start -= 1
    return "\n".join(lines[start:idx + 1]).strip()


def main() -> int:
    dry = "--dry-run" in sys.argv
    changed = []
    for sp in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(sp)
        hit = 0
        for r in rows:
            ex = (r.get("excerpt") or "").strip()
            if len(ex) >= MIN:
                continue
            lp = (r.get("local_path") or "").strip()
            if not lp or not (ROOT / lp).is_file():
                continue
            text = (ROOT / lp).read_text(encoding="utf-8", errors="ignore")
            if ex and ex not in text:      # 摘录不在快照里：不在这里改，交给 repair_data_quality
                continue
            new = expand(text, ex)
            if len(new) > len(ex) and ex in new:
                r["excerpt"] = new
                hit += 1
                changed.append((r.get("source_id"), len(ex), len(new)))
        if hit and not dry:
            write(sp, hdr, rows)
        if hit:
            print(f"{sp.name}: 扩展 {hit} 条")
    for sid, a, b in changed[:10]:
        print(f"  {sid}: {a} -> {b} 字")
    print(f"共 {len(changed)} 条" + ("（dry-run 未写盘）" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
