"""从民政部《县以上行政区划代码》页面补 region.csv 缺失的县级行。

背景：region 表最初是从 area 表反推的，只含「已有片区的县」（857 个），
因此想把片区补建到没有片区的县时，会因缺县码而卡住。
本脚本从民政部公告页解析国标码，只**新增**缺失的县级行，不改动已有行。

用法：
  python scripts/fill_region_counties.py --dry-run
  python scripts/fill_region_counties.py
"""
from __future__ import annotations

import csv
import html as htmllib
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION_CSV = ROOT / "data" / "clean" / "region.csv"
SRC = ROOT / "data" / "stage" / "candidates" / "mca-2023-xzqh.html"
FIELDS = ["region_code", "name", "short_name", "level", "parent_code", "aliases"]

# 只补这几个省（本轮逆向校验涉及的省份），避免一次动太多
WANT_PROV = {"210000": "辽宁", "130000": "河北"}
COUNTY_RE = re.compile(r"^(\d{6})\s*(.+)$")
TAG = re.compile(r"<[^>]+>")
ROW = re.compile(r"<tr\b.*?</tr>", re.S | re.I)
CELL = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S | re.I)


def _clean(cell: str) -> str:
    return htmllib.unescape(TAG.sub("", cell)).replace("\xa0", " ").strip()


def parse_counties(html_text: str) -> list[tuple[str, str, str]]:
    """解析 Excel 导出式表格：每行第一个像六位码的单元格是代码，其后第一个中文单元格是名称。"""
    out: list[tuple[str, str, str]] = []
    cur_city = ""
    for row in ROW.findall(html_text):
        cells = [_clean(c) for c in CELL.findall(row)]
        cells = [c for c in cells if c]
        if not cells:
            continue
        code = next((c for c in cells if re.fullmatch(r"\d{6}", c)), "")
        if not code or not (code.startswith("21") or code.startswith("13")):
            continue
        name = next((c for c in cells if re.search(r"[\u4e00-\u9fa5]", c)), "")
        if not name:
            continue
        if code[2:] == "0000":
            continue
        if code[4:] == "00":
            cur_city = code
            continue
        out.append((code, name, cur_city))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    if not SRC.exists():
        print(f"缺源文件 {SRC.relative_to(ROOT)}，先用 curl 下载民政部页面")
        return 1

    counties = parse_counties(SRC.read_text(encoding="utf-8", errors="replace"))
    print(f"从页面解析出辽宁/河北县级行 {len(counties)} 条")

    with REGION_CSV.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        header = list(rd.fieldnames or FIELDS)
        rows = [r for r in rd if any(r.values())]
    have = {r["region_code"] for r in rows}
    print(f"region.csv 现有 {len(rows)} 行，其中辽宁/河北 {sum(1 for r in rows if r['region_code'][:2] in ('21','13'))} 行")

    added = []
    for code, name, city in counties:
        if code in have:
            continue
        added.append({
            "region_code": code,
            "name": name,
            "short_name": "",
            "level": "county",
            "parent_code": city or "",
            "aliases": "",
        })
        have.add(code)

    print(f"待新增 {len(added)} 行")
    for a in added[:40]:
        print(f"  {a['region_code']} {a['name']}  (市 {a['parent_code']})")
    if len(added) > 40:
        print(f"  …… 另 {len(added) - 40} 行")

    if not dry and added:
        with REGION_CSV.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows + added)
        print(f"已写入 {REGION_CSV.relative_to(ROOT)}")
    elif dry:
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
