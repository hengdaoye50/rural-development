"""核实上海 P310023 是否点名崇明两个片区。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

r = conn.execute(
    "SELECT title, local_path, issuer_level, county_code FROM policy WHERE policy_id='P310023'"
).fetchone()
print(f"P310023 [{r['issuer_level']} 县{r['county_code'] or '-'}] {r['title'][:60]}")
text = (ROOT / r["local_path"]).read_text(encoding="utf-8")

for kw in ("畜禽养殖", "高端设施农业", "生鲜蔬果", "农旅融合"):
    for m in re.finditer(kw, text):
        seg = text[max(0, m.start() - 70): m.end() + 70].replace("\n", " ")
        print(f"  [{kw}] …{seg}…")
        break
