"""用民政部《2023年中华人民共和国县以上行政区划代码》补 region 表的省/市级行。

背景（2026-11-18 接手第二轮发现）：`region` 表有 206 个市级行，但县级行的
`parent_code` 引用了 **133 个 region 里不存在的市码**（广西 8 个、四川 15 个、
云南 15 个……）。后果：按市聚合会静默丢行；`validate_db` 只对 area.city_code
报警，管不到 region 自身。

本脚本**只补 province / city 两级**，不补县级：
  - 补县级会改变「县级单位 2856」这个分母，进而改变县覆盖率口径（属另一项裁定）
  - 省/市级只是父节点，补上不改任何分母

数据源：`data/stage/candidates/mca-2023-xzqh.html`（民政部乡镇以上代码表，Excel 导出的 HTML）。
解析：取每行里「6 位数字码 + 中文名」，按码后缀定级：
  XX0000 → province；XXXX00 → city；其余 → county（跳过）
父码：province 无父；city 父为 XX0000。

约束：
  - 只增不改：已存在的 region_code 一律保留原值（名称不一致只打印告警）
  - 幂等：重复运行不再新增
  - 先 `--dry-run` 看会加哪些行

用法：
  python scripts/backfill_region_from_mca.py --dry-run
  python scripts/backfill_region_from_mca.py
  python scripts/backfill_region_from_mca.py --src data/stage/candidates/mca-2023-xzqh.html
"""
from __future__ import annotations

import csv
import html
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION = ROOT / "data" / "clean" / "region.csv"
DB = ROOT / "data" / "db" / "片区库.sqlite3"
SRC = ROOT / "data" / "stage" / "candidates" / "mca-2023-xzqh.html"

CODE6 = re.compile(r"\b(\d{6})\b")
CJK = re.compile(r"^[\u4e00-\u9fa5（）()·]+$")

# 民政部代码表里没有、但县级行 parent 引用了的「管理性分组」
# 直辖市不设地级市，代码表的县级行父码仍是 X100（市辖区）/X200（县）；
# 419000/429000 是省直辖县级行政区划。这些不是真实地级市，按惯例保留分组名。
MANUAL = {
    "110100": "市辖区", "120100": "市辖区", "500100": "市辖区", "500200": "县",
    "419000": "省直辖县级行政区划", "429000": "省直辖县级行政区划",
}


def parse_mca(path: Path) -> dict[str, str]:
    """返回 {code: name}，只收省/市级（XX0000 / XXXX00）。"""
    text = path.read_text(encoding="utf-8", errors="ignore")
    # 每个 <td> 内容取出；按行（<tr ...> ... </tr>）分组
    out: dict[str, str] = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)]
        if len(cells) < 2:
            continue
        code = name = None
        for c in cells:
            if c.isdigit() and len(c) == 6 and code is None:
                code = c
            elif CJK.match(c) and not c.isdigit() and name is None and len(c) >= 2:
                name = c
        if not code or not name:
            continue
        if code.endswith("0000") or code.endswith("00"):
            out.setdefault(code, name)
    return out


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    src = Path(args[args.index("--src") + 1]) if "--src" in args else SRC
    if not src.exists():
        print(f"读不到 {src}")
        return 2
    mca = parse_mca(src)
    print(f"民政部代码表解析出省/市级 {len(mca)} 个码")

    header, rows = _read(REGION)
    have = {r["region_code"]: r.get("name") for r in rows}
    need_parents: dict[str, int] = {}
    if DB.exists():
        con = sqlite3.connect(DB)
        for parent, n in con.execute(
                "select parent_code, count(*) from region where level='county' "
                "and coalesce(parent_code,'')<>'' group by parent_code"):
            if parent not in have:
                need_parents[parent] = n
    print(f"region 缺父码 {len(need_parents)} 个（县级行引用但表里没有）")

    added, skipped, mismatch = 0, 0, 0
    for code in sorted(need_parents):
        if code in have:
            continue
        name = mca.get(code) or MANUAL.get(code)
        if not name:
            print(f"  !! {code} 在民政部表里找不到，跳过（需人工）")
            skipped += 1
            continue
        level = "province" if code.endswith("0000") else "city"
        parent = "" if level == "province" else code[:2] + "0000"
        rows.append({
            "region_code": code, "name": name, "short_name": name.rstrip("市"),
            "level": level, "parent_code": parent, "aliases": "",
        })
        added += 1
        print(f"  + {code} {name} ({level}, parent {parent or '-'}, 下辖县级 {need_parents[code]})")

    # 已存在但名称不一致：只告警，不改（可能是有意保留的历史名）
    for code in need_parents:
        if code in have and mca.get(code) and have[code] != mca[code]:
            mismatch += 1
            print(f"  ~ {code} 现值「{have[code]}」，民政部作「{mca[code]}」（不改，仅提示）")

    if not dry and added:
        _write(REGION, header, rows)
    print(f"\n{'dry-run，' if dry else ''}新增 {added} 行 / 无法补齐 {skipped} 个 / 名称不一致 {mismatch} 个")
    if added and not dry:
        print("接着跑：merge_by_province（可选）-> build_db -> validate_db -> health_report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
