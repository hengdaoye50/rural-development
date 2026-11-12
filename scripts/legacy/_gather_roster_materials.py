"""取齐本轮补建所需材料：belt 表约束、湖北 20 条样板带全名、河北 22 条片区全名与县码。"""
import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

print("=== belt 建表约束 ===")
sql = conn.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='belt'"
).fetchone()[0]
print(sql)

# region 名 → 码
region = {}
with (ROOT / "data" / "clean" / "region.csv").open(encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["level"] == "county":
            region[r["name"]] = (r["region_code"], r["parent_code"])

print("\n=== 湖北 20 条样板带 ===")
t = (ROOT / "data/raw/HB/20261107-hb-sheng-shoupi-20tiao-yangbandai-mingdan/原文.md").read_text(encoding="utf-8")
tail = t[t.find("样板带名单"):]
lines = [x.strip() for x in tail.splitlines() if x.strip().endswith("样板带")]
for i, ln in enumerate(lines, 1):
    m = re.match(r"^([\u4e00-\u9fa5]{2,8}?(?:区|县|市))", ln)
    unit = m.group(1) if m else "?"
    code, city = region.get(unit, ("?", ""))
    print(f"  {i:>2}. {ln}   → {unit} {code} 市={city}")

print("\n=== 河北 22 条省级重点片区 ===")
t2 = (ROOT / "data/raw/HE/20250221-he-sheng-2025-pianqu-jingzhengxing-linxuan-tongzhi/原文.md").read_text(encoding="utf-8")
entries = re.findall(r"\d+\.\s*([^\n]{4,60}?和美乡村重点片区[^\n]*)", t2)
for i, e in enumerate(entries, 1):
    m = re.match(r"^([\u4e00-\u9fa5]{2,10}?(?:满族蒙古族自治县|满族自治县|自治县|区|县|市))", e)
    unit = m.group(1) if m else "?"
    code, city = region.get(unit, ("?", ""))
    print(f"  {i:>2}. {e}   → {unit} {code} 市={city}")
