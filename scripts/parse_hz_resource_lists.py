# -*- coding: utf-8 -*-
"""解析「杭州市片区资源清单」系列正文，抽取片区名并与库内比对（只读）。

输出：reports/qa/杭州片区资源清单-对账.md + .csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "ZJ" / "2026-hz-resource-lists"
OUT_MD = ROOT / "reports" / "qa" / "杭州片区资源清单-对账.md"
OUT_CSV = ROOT / "reports" / "qa" / "杭州片区资源清单-对账.csv"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+")

DISTRICT = {
    "yuhang": "余杭区", "qiantang": "钱塘区", "fuyang": "富阳区", "chunan": "淳安县",
    "linping": "临平区", "tonglu": "桐庐县", "jiande": "建德市", "xihu": "西湖区",
    "linan": "临安区", "xiaoshan": "萧山区",
}


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def parse_file(p: Path) -> tuple[str, list[dict]]:
    lines = [x.strip() for x in p.read_text(encoding="utf-8").splitlines()]
    found: list[dict] = []
    for i, s in enumerate(lines):
        if not s or len(s) > 20:
            continue
        if not s.endswith("片区"):
            continue
        if any(w in s for w in ("位于", "包括", "带动", "辐射", "覆盖", "重点村")):
            continue
        # 取后文里「以XX村为重点村」与面积
        key_village = ""
        area = ""
        for j in range(i + 1, min(i + 12, len(lines))):
            m = re.search(r"以(.{2,12}?村)为重点村", lines[j])
            if m and not key_village:
                key_village = m.group(1)
            m2 = re.search(r"区域面积([\d.]+)平方公里", lines[j])
            if m2 and not area:
                area = m2.group(1)
        if not any(x["name"] == s for x in found):
            found.append({"name": s, "key_village": key_village, "area_km2": area})
    return found


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{ROOT/'data/db/片区库.sqlite3'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "select area_id,name,name_norm,county_code,status from area "
        "where province_code='330000' and record_state='active'")]
    by_norm = {r["name_norm"]: r for r in rows}
    county_name = {r["region_code"]: r["name"] for r in con.execute(
        "select region_code,name from region where level='county'")}

    out: list[dict] = []
    per_district: dict[str, list[dict]] = {}
    for p in sorted(SRC.glob("*.md")):
        key = p.stem
        items = parse_file(p)
        per_district[DISTRICT.get(key, key)] = items
        for it in items:
            n = norm(it["name"])
            hit = by_norm.get(n)
            if not hit:
                # 宽松匹配：库内名字包含该名
                cand = [r for r in rows if n and n in r["name_norm"]]
                hit = cand[0] if cand else None
            out.append({
                "district": DISTRICT.get(key, key),
                "name": it["name"],
                "key_village": it["key_village"],
                "area_km2": it["area_km2"],
                "in_db": "是" if hit else "否",
                "area_id": hit["area_id"] if hit else "",
                "db_name": hit["name"] if hit else "",
                "db_county": county_name.get(hit["county_code"], "") if hit else "",
                "db_status": hit["status"] if hit else "",
            })

    total = len(out)
    miss = [x for x in out if x["in_db"] == "否"]
    print(f"解析 {len(per_district)} 个区县、{total} 个片区｜在库 {total-len(miss)}｜缺 {len(miss)}")
    for d, items in per_district.items():
        print(f"  {d}: {len(items)} 个")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else [], lineterminator="\r\n")
        w.writeheader()
        w.writerows(out)

    lines = ["# 杭州「片区资源清单」系列 · 与库内对账", "",
             f"共解析 **{len(per_district)}** 个区县、**{total}** 个片区；在库 **{total-len(miss)}**，缺 **{len(miss)}**。", ""]
    for d, items in per_district.items():
        lines.append(f"## {d}（{len(items)}）")
        lines.append("")
        lines.append("| 片区 | 重点村 | 面积 km² | 在库 | area_id | 库内状态 |")
        lines.append("|---|---|---|---|---|---|")
        for x in [y for y in out if y["district"] == d]:
            lines.append(f"| {x['name']} | {x['key_village'] or '—'} | {x['area_km2'] or '—'} | "
                         f"{x['in_db']} | {x['area_id'] or '—'} | {x['db_status'] or '—'} |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("->", OUT_MD.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
