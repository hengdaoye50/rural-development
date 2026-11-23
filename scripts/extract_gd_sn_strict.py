# -*- coding: utf-8 -*-
"""从已落盘正文重新严格抽取片区名（不入库）。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(".")
RAW = ROOT / "data" / "raw"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+")
GEN = ("片区组团", "片区化", "片区发展", "片区建设", "片区治理", "片区党建", "片区项目", "片区名单",
       "片区资源", "片区运营", "片区协作", "片区联动", "片区共建", "片区共富", "片区示范", "片区创建",
       "片区推进", "片区工作", "片区模式", "片区经验", "片区规划", "片区产业", "片区振兴")

QUOTED = re.compile(r"[“「【]([\u4e00-\u9fa5A-Za-z0-9·]{2,24}?片区)[”」】]")
QUALIFIED = re.compile(r"([\u4e00-\u9fa5]{2,10}(?:镇|村|街道|乡)[\u4e00-\u9fa5]{0,12}片区)")
COUNTY_LEAD = re.compile(r"([\u4e00-\u9fa5]{2,8}(?:县|区|市|旗)(?:[\u4e00-\u9fa5]{0,12})?片区)")


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    region = {}
    for line in (ROOT / "data/clean/region.csv").read_text(encoding="utf-8-sig").splitlines()[1:]:
        p = line.split(",")
        if len(p) >= 4 and p[3] == "county":
            region.setdefault(p[1], set()).add(p[0])

    hits: dict[str, dict] = {}
    for abbr in ("GD", "SN"):
        for f in sorted((RAW / abbr).glob("*/原文.md")):
            text = f.read_text(encoding="utf-8")
            for pat in (QUOTED, QUALIFIED, COUNTY_LEAD):
                for m in pat.finditer(text):
                    name = m.group(1)
                    if any(name == g or name.endswith(g) for g in GEN):
                        continue
                    if len(name) < 4:
                        continue
                    # 名字里自带县区（优先），否则上下文找
                    code, county = "", ""
                    for nm, codes in region.items():
                        if nm in name and len(nm) >= 2 and len(codes) == 1:
                            code, county = next(iter(codes)), nm
                            break
                    if not code:
                        ctx = text[max(0, m.start() - 80):m.end() + 40]
                        for nm, codes in region.items():
                            if nm in ctx and len(nm) >= 2 and len(codes) == 1:
                                code, county = next(iter(codes)), nm
                                break
                    key = (abbr, norm(name))
                    h = hits.setdefault(key, {"abbr": abbr, "name": name, "county": county,
                                              "code": code, "n": 0, "file": str(f)})
                    h["n"] += 1
                    if code and not h["code"]:
                        h["code"], h["county"] = code, county
    rows = sorted(hits.values(), key=lambda x: (-x["n"], x["name"]))
    print(f"严格抽取 {len(rows)} 个；有县区 {sum(1 for r in rows if r['code'])} 个")
    for r in rows[:60]:
        print(f"{r['abbr']} {r['name']}｜{r['county']}({r['code']})｜×{r['n']}")
    out = ROOT / "data/stage/candidates/gd-sn-strict.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["abbr", "name", "county", "code", "n", "file"],
                           lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print("->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
