# -*- coding: utf-8 -*-
"""从 21 个省厅页面里抽取「XX片区」候选，并与库内比对（只读）。"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "ZJ" / "2026-nynct"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+")
GEN = ("片区组团", "片区化", "片区发展", "片区建设", "片区治理", "片区党建", "片区联合",
       "片区项目", "片区名单", "片区资源", "片区运营", "片区协作", "片区联动", "片区共建",
       "片区共富", "片区振兴", "片区示范", "片区创建", "片区推进", "片区工作", "片区模式",
       "片区经验", "片区规划", "片区产业", "片区组团式")

PAT = re.compile(r"([\u4e00-\u9fa5A-Za-z0-9·]{2,18}?片区)")


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{ROOT/'data/db/片区库.sqlite3'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    db = [dict(r) for r in con.execute(
        "select area_id,name,name_norm from area where province_code='330000' and record_state='active'")]
    names = {r["name_norm"]: r for r in db}

    for p in sorted(SRC.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        toks = Counter()
        for m in PAT.finditer(text):
            t = m.group(1)
            if any(g == t or t.endswith(g) for g in GEN):
                continue
            if len(t) < 3:
                continue
            toks[t] += 1
        if not toks:
            continue
        print(f"\n== {p.name}")
        for t, n in toks.most_common(12):
            nz = norm(t)
            hit = names.get(nz)
            tag = f"库内 {hit['area_id']}" if hit else "缺"
            print(f"   {t} ×{n}  [{tag}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
