# -*- coding: utf-8 -*-
"""二轮 excerpt 重锚：difflib 最长公共块 + 长 CJK 串定位，把 digest 拉回 verbatim。

一轮只按「片区名」锚定，190 条没救回来。二轮换策略：
  1. 取 excerpt 里最长的连续中文串（>=6 字），在快照里找；
  2. 用 difflib.SequenceMatcher 在归一化文本上找最长匹配块（>=12 字），命中即取该块在原文的窗口；
  3. 都不中 → 保持 digest（不编造）。

只写 `data/clean/by_province/`，跑完 merge -> build -> validate。
"""
from __future__ import annotations

import csv
import difflib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
PUN = re.compile(r"[\s\u3000\W_]+", re.U)
CJK = re.compile(r"[\u4e00-\u9fa5]{6,}")


def read(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p, hdr, rows):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    os.replace(tmp, p)


def main() -> int:
    dry = "--dry-run" in sys.argv
    stats = dict(tried=0, cjk_hit=0, block_hit=0, left=0)
    for sp in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(sp)
        ch = False
        for s in rows:
            if (s.get("excerpt_status") or "") != "digest":
                continue
            lp = (s.get("local_path") or "").strip()
            if not lp:
                continue
            f = ROOT / lp
            if not f.is_file():
                continue
            ex = (s.get("excerpt") or "").strip()
            if len(ex) < 20:
                continue
            stats["tried"] += 1
            text = f.read_text(encoding="utf-8", errors="ignore")
            norm_t = PUN.sub("", text)
            hit = None
            # 1) 最长 CJK 串
            runs = sorted(CJK.findall(ex), key=len, reverse=True)[:5]
            for r in runs:
                pos = text.find(r)
                if pos >= 0:
                    a, b = max(0, pos - 80), min(len(text), pos + len(r) + 160)
                    hit = text[a:b].replace("\n", " ").strip()
                    stats["cjk_hit"] += 1
                    break
            # 2) difflib 最长块
            if not hit:
                norm_e = PUN.sub("", ex)
                sm = difflib.SequenceMatcher(None, norm_e, norm_t, autojunk=False)
                m = sm.find_longest_match(0, len(norm_e), 0, len(norm_t))
                if m.size >= 12:
                    # 用块首尾在原文里定位（归一化后索引 -> 原文近似：取块文本原样找）
                    block = norm_t[m.b:m.b + m.size]
                    pos = text.find(block[:min(20, len(block))])
                    if pos >= 0:
                        a, b = max(0, pos - 60), min(len(text), pos + m.size + 120)
                        hit = text[a:b].replace("\n", " ").strip()
                        stats["block_hit"] += 1
            if hit and len(hit) >= 20:
                s["excerpt"] = hit
                s["excerpt_status"] = "verbatim"
                ch = True
            else:
                stats["left"] += 1
        if ch and not dry:
            write(sp, hdr, rows)
    print(("dry-run：" if dry else "已完成：") + str(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
