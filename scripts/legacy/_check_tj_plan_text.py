"""一次性：在天津市级示范区实施方案全文里查静海/古蕴的表述，判断 A120007 的映射依据。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
c.row_factory = sqlite3.Row

rows = c.execute(
    "SELECT policy_id, title, local_path FROM policy "
    "WHERE province_code = '120000' AND title LIKE '%示范片区%'"
).fetchall()
for r in rows:
    print(r["policy_id"], r["title"])
    p = ROOT / r["local_path"]
    if not p.exists():
        print("  存档缺失", r["local_path"])
        continue
    text = p.read_text(encoding="utf-8")
    for kw in ("静海", "古蕴", "台头", "独流", "北二堡"):
        idx = text.find(kw)
        print(f"  {kw}: {'命中 @'+str(idx) if idx >= 0 else '无'}")
        if idx >= 0:
            print("    …", text[max(0, idx - 60): idx + 90].replace("\n", " "), "…")
