"""精确核对河南 2025 年首批 16 个先导区：哪些县在库内没有任何片区。"""
import csv
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

ROSTER = [
    ("潢川县", "创制型"), ("嵩县", "创制型"), ("西峡县", "创制型"), ("新安县", "创制型"),
    ("灵宝市", "创制型"), ("光山县", "创制型"), ("兰考县", "创制型"),
    ("济源示范区大沟河", "创制型"), ("新乡县", "创制型"), ("周口市淮阳区", "创制型"),
    ("中牟县", "培育型"), ("宁陵县", "培育型"), ("罗山县", "培育型"),
    ("南阳市卧龙区", "培育型"), ("内黄县", "培育型"), ("林州市", "培育型"),
]

covered = set()
for tbl in ("area", "belt"):
    for r in conn.execute(
        f"SELECT county_code FROM {tbl} WHERE province_code='410000' AND record_state='active'"
    ):
        if r["county_code"]:
            covered.add(r["county_code"])

print(f"库内河南覆盖 {len(covered)} 个县\n")
missing = []
for nm, typ in ROSTER:
    key = nm.replace("周口市", "").replace("南阳市", "")
    code = name2code.get(nm) or name2code.get(key) or ""
    if not code:
        # 试包含匹配
        code = next((c for n, c in name2code.items() if n in nm or nm in n), "")
    ok = code in covered
    print(f"  {typ} {nm:<14} {code or '码未找到':<8} {'已覆盖' if ok else '★库内无'}")
    if code and not ok:
        missing.append((nm, code, typ))

print(f"\n库内无片区的先导区：{len(missing)} 个")
for nm, code, typ in missing:
    print(f"  {nm} {code} ({typ})")
