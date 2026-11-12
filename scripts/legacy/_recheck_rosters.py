"""核对辽宁/河北/湖北三份省级名单的对账完成度（按县码比对，避免名称写法差异）。"""
import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

name2code = {}
with (ROOT / "data" / "clean" / "region.csv").open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["level"] == "county":
            name2code[r["name"]] = r["region_code"]


def resolve(text: str) -> str:
    """从名单条目里尽量解析出县级码：优先精确县名，其次包含匹配。"""
    for nm, code in name2code.items():
        if len(nm) >= 2 and nm in text:
            return code
    return ""


def covered(prov: str) -> set[str]:
    out = set()
    for r in conn.execute(
        "SELECT county_code FROM area WHERE province_code=? AND record_state='active'",
        (prov,),
    ):
        out.add(r["county_code"])
    for r in conn.execute(
        "SELECT county_code FROM belt WHERE province_code=? AND record_state='active' "
        "AND county_code IS NOT NULL AND county_code != ''",
        (prov,),
    ):
        out.add(r["county_code"])
    return out


CASES = [
    ("210000", "辽宁·2023省级示范带23条",
     "data/raw/LN/20230426-ln-sheng-nongwei-2023-shifandai-mingdan/原文.md",
     r"\d+\.\s*([^\n]{2,90}?)\s*乡村振兴示(?:范带|范\s*\n?\s*带)?"),
    ("130000", "河北·省级重点片区22条",
     "data/raw/HE/20250221-he-sheng-2025-pianqu-jingzhengxing-linxuan-tongzhi/原文.md",
     r"\d+\.\s*([\u4e00-\u9fa5][^\n]{2,50}?和美乡村重点片区[^\n]*)"),
    ("420000", "湖北·首批20条样板带",
     "data/raw/HB/20261107-hb-sheng-shoupi-20tiao-yangbandai-mingdan/原文.md",
     r"([\u4e00-\u9fa5][^\n]{2,50}?样板带)"),
]

for prov, label, rel, pat in CASES:
    p = ROOT / rel
    print("=" * 70)
    print(label)
    if not p.exists():
        print("  原文缺失")
        continue
    text = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"))
    entries = [m.group(1).strip() for m in re.finditer(pat, text)]
    codes = [resolve(e) for e in entries]
    uniq = {c for c in codes if c}
    db = covered(prov)
    miss = sorted(uniq - db)
    print(f"  名单 {len(entries)} 条，解析出县码 {len(uniq)} 个")
    print(f"  库内覆盖县 {len(db)} 个")
    print(f"  名单内但库内无：{len(miss)} 个 {'、'.join(miss) if miss else '（已全覆盖）'}")
    unresolved = [e for e, c in zip(entries, codes) if not c]
    if unresolved:
        print(f"  未能解析县码 {len(unresolved)} 条：")
        for u in unresolved[:4]:
            print(f"    - {u[:60]}")
