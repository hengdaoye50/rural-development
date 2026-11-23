# -*- coding: utf-8 -*-
"""把严格抽取里「自带镇/村/街道/乡限定 + 县区唯一」的片区汇成可入库候选（运行中）。

输出：data/stage/candidates/area-gdsn.csv（GD 与 SN 合表，ingest 时按省拆分）
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(".")
BAD = ("打造", "入选", "探索", "推进", "关于", "以", "的", "和", "与", "及", "个", "批", "首批",
       "省", "全市", "全县", "各", "该", "此", "这", "为", "是", "在", "将", "已", "把", "从", "对",
       "镇村片区", "典型村片区", "和美乡村", "美丽村庄", "示范片区", "产业片区", "乡村旅游")
LOC = re.compile(r"(镇|村|街道|乡)")
OK = re.compile(r"^[\u4e00-\u9fa5]{2,22}片区$")


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+", "", s)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = list(csv.DictReader(open("data/stage/candidates/gd-sn-strict.csv", encoding="utf-8-sig")))
    # 文章正文索引：找句子做 excerpt
    keep = []
    for r in rows:
        name = r["name"].strip()
        if not OK.match(name):
            continue
        if not LOC.search(name):
            continue
        if any(b in name for b in BAD):
            continue
        if len(name) < 6 or not r["code"]:
            continue
        keep.append(r)
    # 同名去重，取出现次数最多
    best: dict[tuple[str, str], dict] = {}
    for r in keep:
        k = (r["abbr"], norm(r["name"]))
        if k not in best or int(r["n"]) > int(best[k]["n"]):
            best[k] = r
    sel = sorted(best.values(), key=lambda x: -int(x["n"]))
    print(f"入选 {len(sel)} 条（GD {sum(1 for x in sel if x['abbr']=='GD')} / "
          f"SN {sum(1 for x in sel if x['abbr']=='SN')}）")
    for r in sel[:40]:
        print(f"  {r['abbr']} {r['name']}｜{r['county']}({r['code']})×{r['n']}")
    out = ROOT / "data/stage/candidates/area-gdsn.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["abbr", "name", "county", "code", "n", "file"],
                           lineterminator="\r\n")
        w.writeheader()
        w.writerows(sel)
    print("->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
