"""找湖州市第二批新时代美丽乡村样板片区名单那条 policy（ZJ05 报告称正文点名「诗画琏溪」但 areas 未挂）。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, title, local_path FROM policy "
    "WHERE title LIKE '%样板片区%' OR title LIKE '%美丽乡村%名单%' ORDER BY policy_id"
):
    body = ROOT / r["local_path"]
    text = body.read_text(encoding="utf-8") if body.exists() else ""
    if "诗画琏溪" in text or "琏溪" in text:
        print(f"{r['policy_id']}  {r['title'][:60]}")
        i = text.find("诗画琏溪")
        if i < 0:
            i = text.find("琏溪")
        print("    …", text[max(0, i - 90): i + 90].replace("\n", " "), "…")
