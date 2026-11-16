"""核对赣州 18 县报告里点名的 10 个片区，哪些是库内没有的。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

CANDS = [
    ("360703", "唐江-十八塘示范带"),
    ("360724", "上江线四融一共示范带"),
    ("360724", "上太线四融一共示范带"),
    ("360725", "赣丰线示范带"),
    ("360725", "思杰线示范带"),
    ("360725", "上寡线示范带"),
    ("360725", "聂文线示范带"),
    ("360725", "过埠片区"),
    ("360726", "百里产业示范带"),
    ("360727", "赣南先行区"),
]

existing = [(r["county_code"], r["name"]) for r in conn.execute(
    "SELECT county_code, name FROM area WHERE province_code='360000'")]

print("江西库内现有片区：")
for cc, nm in existing:
    print(f"  {cc} {nm}")
print()

for cc, nm in CANDS:
    key = nm.replace("四融一共", "").replace("-", "").replace("—", "")
    hit = [e for e in existing if e[0] == cc]
    dup = [e[1] for e in hit if key[:6] in e[1] or e[1][:6] in nm]
    print(f"{nm:<22} 县{cc} 库内该县已有:{'、'.join(n for _, n in hit) or '无'} "
          f"→ {'疑重复' if dup else '★新'}")
