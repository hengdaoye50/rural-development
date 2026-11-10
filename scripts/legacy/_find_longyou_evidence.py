"""查含「鱼跃龙门」「畲乡薏谷」的既有 policy（ZJ08 代理报告称其 areas 为空，需补挂 A330202/A330203）。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, title, url, local_path FROM policy "
    "WHERE local_path LIKE '%longyou%' OR title LIKE '%发展轴%' OR title LIKE '%龙游%'"
):
    body = ROOT / r["local_path"]
    hit = ""
    if body.exists():
        text = body.read_text(encoding="utf-8")
        for kw in ("鱼跃龙门", "畲乡薏谷"):
            if kw in text:
                hit += kw + " "
    print(f"{r['policy_id']} {'['+hit.strip()+']' if hit else ''} {r['title'][:58]}")
    print(f"    {r['url'][:90]}")
