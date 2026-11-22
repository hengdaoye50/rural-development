# -*- coding: utf-8 -*-
"""清理 `area.name` / `name_norm` 里的引号残留（OCR 与名单转录常见）。

为什么需要：名单原文常写作「“上农智田·于河印象”乡村振兴示范片区」，OCR/转录时半角全角混用，
容易只掉前引号留下后引号（`上农智田·于河印象”乡村振兴示范片区`），名称即被污染。
官方名称的引号是排版符号，不是名的一部分；库内既有记录（如山东第五批）本就无引号，故统一去除。

只写 `data/clean/by_province/*-area.csv`（area 是实体表，merge 会重建 master）。

用法：
  python scripts/fix_area_name_quotes.py --dry-run
  python scripts/fix_area_name_quotes.py
跑完接 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
QUOTES = "\u201c\u201d\u2018\u2019\"'"


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


def strip_q(s: str) -> str:
    return "".join(c for c in (s or "") if c not in QUOTES).strip()


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        hit = 0
        for r in rows:
            for k in ("name", "name_norm"):
                old = r.get(k) or ""
                new = strip_q(old)
                if new != old:
                    r[k] = new
                    hit += 1
        if hit:
            total += hit
            print(f"{p.name}: {hit} 个字段去掉引号")
            if not dry:
                write(p, hdr, rows)
    print(f"共 {total} 个字段" + ("（dry-run 未写盘）" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
