"""region 表结构完整性修补。

两类问题（2026-11 扫描发现）：

1. **缺市级行**：area 表的 city_code 引用了 14 个 region 里根本不存在的市码
   （河北 6 个、辽宁 8 个），于是按市聚合、按市下钻全部失效。
   补名依据是**该市下辖的县级行**——父码指向同一 city_code 的一组县级单位，
   其构成与该市一致（如 130200 下有路南区/路北区/古冶区/开平区/丰南区/丰润区/
   曹妃甸区/滦南县，即唐山市）。名称按 GB/T 2260。

2. **退休码占位**：龙南 2020 撤县设市后国标码为 360783，360727 是旧龙南县码。
   region 里两行同名「龙南市」，需把 360727 改回历史名并标注停用，
   否则按名匹配会随机命中一个。

只改 `data/clean/region.csv`（region 不在 by_province 分片范围内）。

    python scripts/fix_region_integrity.py --dry-run
    python scripts/fix_region_integrity.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION = ROOT / "data" / "clean" / "region.csv"
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# city_code, 名称, 省码  —— 名称按 GB/T 2260，可行性由该市下辖县级行印证（见模块说明）
MISSING_CITIES: list[tuple[str, str, str]] = [
    ("130200", "唐山市", "130000"),
    ("130300", "秦皇岛市", "130000"),
    ("130600", "保定市", "130000"),
    ("130800", "承德市", "130000"),
    ("130900", "沧州市", "130000"),
    ("131100", "衡水市", "130000"),
    ("210600", "丹东市", "210000"),
    ("210700", "锦州市", "210000"),
    ("210800", "营口市", "210000"),
    ("210900", "阜新市", "210000"),
    ("211000", "辽阳市", "210000"),
    ("211200", "铁岭市", "210000"),
    ("211300", "朝阳市", "210000"),
    ("211400", "葫芦岛市", "210000"),
]

# region_code, 现名, 应名, aliases, 说明
RENAME: list[tuple[str, str, str, str, str]] = [
    ("360727", "龙南市", "龙南县", "龙南市（2020 撤县设市，代码改用 360783）",
     "与 360783 龙南市重名；按国标恢复历史名，避免按名匹配随机命中"),
    # ---- 退休码：原为 name==code 的占位行，按撤县设市/设区沿革恢复历史名 ----
    ("331021", "331021", "玉环县", "2017 撤县设市，现 331083 玉环市", "占位行恢复历史名；已无片区挂在该码上"),
    ("341822", "341822", "广德县", "2019 撤县设市，现 341882 广德市", "占位行恢复历史名"),
    ("360782", "360782", "南康市", "2013 撤市设区，现 360703 南康区", "占位行恢复历史名"),
    ("411626", "411626", "淮阳县", "2019 撤县设区，现 411603 淮阳区", "占位行恢复历史名"),
    ("520421", "520421", "平坝县", "2014 撤县设区，现 520403 平坝区", "占位行恢复历史名"),
    ("522322", "522322", "兴仁县", "2018 撤县设市，现 522302 兴仁市", "占位行恢复历史名"),
    ("610521", "610521", "华县", "2015 撤县设区，现 610503 华州区", "占位行恢复历史名"),
    ("469000", "469000", "省直辖县级行政区划", "海南省对省直辖县级市/县的汇总码，非实体政区", "占位行改为其真实含义"),
]
# 仍待核实的占位码（不敢猜，留给权威源）：441228 / 500126 / 510724 / 620171
UNRESOLVED = ("441228", "500126", "510724", "620171")


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, cols: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    cols, rows = _read(REGION)
    if not cols:
        print(f"读不到 {REGION}")
        return 1
    have = {r["region_code"] for r in rows}

    # 校验：待补的市码必须真的被县级行引用，否则说明码本身错了
    if DB.exists():
        con = sqlite3.connect(DB)
        children = {}
        for code, parent in con.execute(
                "select region_code, parent_code from region where level='county'"):
            children.setdefault(parent, []).append(code)
        for code, name, _ in MISSING_CITIES:
            kids = children.get(code, [])
            print(f"  {code} {name}: 下辖县级行 {len(kids)} 个"
                  + (f"，如 {kids[:3]}" if kids else "  ← 无县级行，需人工核实"))

    added = 0
    for code, name, prov in MISSING_CITIES:
        if code in have:
            print(f"  已存在 {code} {name}，跳过")
            continue
        rows.append({
            "region_code": code, "name": name, "short_name": name.rstrip("市"),
            "level": "city", "parent_code": prov, "aliases": "",
        })
        added += 1
        print(f"  + {code} {name} (city, parent {prov})")

    renamed = 0
    for code, old, new, aliases, why in RENAME:
        hit = [r for r in rows if r["region_code"] == code and r.get("name") == old]
        if not hit:
            stale = [r.get("name") for r in rows if r["region_code"] == code]
            print(f"  跳过 {code} 改名：现值 {stale}")
            continue
        for r in hit:
            r["name"] = new
            if not (r.get("aliases") or "").strip():
                r["aliases"] = aliases
        renamed += len(hit)
        print(f"  {code} name: {old} -> {new}  ({why})")

    print(f"\n新增市级行 {added} / 改名 {renamed}" + ("（dry-run 未写盘）" if dry else ""))
    if not dry and (added or renamed):
        _write(REGION, cols, rows)
        print("已写 region.csv；接着跑：build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
