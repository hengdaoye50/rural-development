"""核实彭泽、分宜、瑞昌三县报告里的片区提法，判断哪些可建 area。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

CASES = [
    ("360430", ["湖光山色", "城郊江边", "先行片区"]),
    ("360521", ["南翼", "北翼", "钤阳湖", "片区"]),
    ("360481", ["黄砂", "赤湖", "示范带"]),
]

for cc, kws in CASES:
    r = conn.execute(
        "SELECT policy_id, title, local_path FROM policy WHERE county_code=? AND doc_type='报告'",
        (cc,),
    ).fetchone()
    if not r:
        print(f"{cc} 无报告")
        continue
    text = (ROOT / r["local_path"]).read_text(encoding="utf-8")
    print("=" * 70)
    print(f"{cc} {r['policy_id']} {r['title'][:40]}")
    for kw in kws:
        for m in list(re.finditer(re.escape(kw), text))[:2]:
            seg = text[max(0, m.start() - 80): m.end() + 80].replace("\n", " ")
            print(f"  [{kw}] …{seg}…")
