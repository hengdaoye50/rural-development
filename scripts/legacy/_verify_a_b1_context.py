"""核实 A 类 2 条与 B1 中最可能有对应关系的 1 条，打印上下文供判断。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

CASES = [
    ("P330259", "亭旁片区"),
    ("P370288", "大户庄园片区"),
    ("P330087", "未来乡村示范带"),
    ("P330484", "中泰街道未来乡村示范带"),
]

for pid, kw in CASES:
    r = conn.execute(
        "SELECT title, local_path, county_code, issuer_level FROM policy WHERE policy_id=?", (pid,)
    ).fetchone()
    if not r:
        print(f"{pid} 不存在")
        continue
    text = (ROOT / r["local_path"]).read_text(encoding="utf-8")
    print("=" * 68)
    print(f"{pid} [{r['issuer_level']} 县{r['county_code'] or '-'}] {r['title'][:50]}")
    n = 0
    for m in re.finditer(re.escape(kw), text):
        seg = text[max(0, m.start() - 60): m.end() + 60].replace("\n", " ")
        print(f"   …{seg}…")
        n += 1
        if n >= 2:
            break
    if n == 0:
        print("   （正文无此词）")
