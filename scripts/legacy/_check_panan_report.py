"""找磐安相关政策的正文是否点名「天山」等片区。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT policy_id, title, local_path FROM policy WHERE title LIKE '%磐安%'"
).fetchall()
print(f"磐安相关 policy {len(rows)} 条")
for r in rows:
    body = ROOT / r["local_path"]
    text = body.read_text(encoding="utf-8") if body.exists() else ""
    hits = [kw for kw in ("天山", "乌石", "墨林", "黄林坑") if kw in text]
    print(f"  {r['policy_id']} {r['title'][:46]}  命中:{hits}")
    for kw in hits[:1]:
        i = text.find(kw)
        print("     …", text[max(0, i - 60): i + 60].replace("\n", " "), "…")
