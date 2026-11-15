"""核实 B1 中最像的三条，打印原文上下文。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

CASES = [
    ("P330143", "慢生活", "A330429 慢享生活片区"),
    ("P330440", "安仁", "A330323 安仁共富联合体片区"),
    ("P330052", "花漾", "A330402 花漾仁和片区"),
]

for pid, kw, note in CASES:
    r = conn.execute(
        "SELECT title, local_path, issuer_level, county_code FROM policy WHERE policy_id=?", (pid,)
    ).fetchone()
    text = (ROOT / r["local_path"]).read_text(encoding="utf-8")
    print("=" * 66)
    print(f"{note}\n  ← {pid} [{r['issuer_level']} 县{r['county_code'] or '-'}] {r['title'][:46]}")
    n = 0
    for m in re.finditer(kw, text):
        seg = text[max(0, m.start() - 70): m.end() + 70].replace("\n", " ")
        print(f"    …{seg}…")
        n += 1
        if n >= 2:
            break
