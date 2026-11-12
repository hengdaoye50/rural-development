"""评估地理维度的现有基础：town_codes 的实际形态与可用性。"""
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT area_id, name, county_code, town_codes, cover_desc FROM area "
    "WHERE record_state='active'"
).fetchall()

kinds = Counter()
samples = {}
for r in rows:
    tc = (r["town_codes"] or "").strip()
    if not tc:
        k = "空"
    elif re.fullmatch(r"\d{9}", tc):
        k = "九位乡镇码"
    elif re.fullmatch(r"[\d/、,，\s]+", tc):
        k = "纯数字（非九位）"
    elif re.search(r"[\u4e00-\u9fa5]", tc):
        k = "中文乡镇名"
    else:
        k = "其它"
    kinds[k] += 1
    samples.setdefault(k, []).append((r["area_id"], tc, r["name"][:20]))

print(f"active 片区 {len(rows)}")
for k, n in kinds.most_common():
    print(f"  {k:<16}{n:>5}  ({n/len(rows)*100:.0f}%)")
    for s in samples[k][:3]:
        print(f"       例：{s[0]} {s[1]!r}  {s[2]}")

print("\n=== cover_desc 能否支撑空间重建 ===")
has_town = sum(1 for r in rows if re.search(r"[\u4e00-\u9fa5]{2,4}(镇|乡|街道)", r["cover_desc"] or ""))
print(f"  cover_desc 里出现乡镇名的：{has_town}/{len(rows)} ({has_town/len(rows)*100:.0f}%)")
has_vill = sum(1 for r in rows if re.search(r"[\u4e00-\u9fa5]{2,4}村", r["cover_desc"] or ""))
print(f"  cover_desc 里出现村名的：  {has_vill}/{len(rows)} ({has_vill/len(rows)*100:.0f}%)")
