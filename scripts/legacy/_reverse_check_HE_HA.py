"""逆向校验·河北 / 河南：用库内已有的省级名单，对账库内片区覆盖的县。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row
region = {
    x["region_code"]: x["name"]
    for x in conn.execute("SELECT region_code, name FROM region WHERE length(region_code)=6")
}


def canon(s: str) -> str:
    return (
        s.replace("满族自治县", "")
        .replace("自治县", "")
        .replace("县", "")
        .replace("市", "")
        .replace("区", "")
        .strip()
    )


def db_units(prov: str) -> set[str]:
    out = set()
    for r in conn.execute(
        "SELECT DISTINCT county_code FROM area WHERE province_code=? AND record_state='active'",
        (prov,),
    ):
        out.add(canon(region.get(r["county_code"], "")))
    return out


CASES = [
    ("130000", "河北", "data/raw/HE/20250221-he-sheng-2025-pianqu-jingzhengxing-linxuan-tongzhi/原文.md"),
    ("410000", "河南", "data/raw/HA/20260707-ha-sheng-2026-hemei-xiangcun-xianndaoyu-mingdan/原文.md"),
]

for prov, name, rel in CASES:
    p = ROOT / rel
    print("=" * 70)
    print(f"{name}  名单：{rel}")
    if not p.exists():
        print("  原文缺失")
        continue
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text)
    print(f"  原文 {len(text)} 字")
    print("  —— 原文 ——")
    print("  " + text.replace("\n", "\n  ")[:2200])
    units = db_units(prov)
    print(f"\n  库内 {name} 有片区的县：{len(units)} 个 → {'、'.join(sorted(units))}")
