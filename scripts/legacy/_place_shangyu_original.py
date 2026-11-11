"""找上虞区发展轴规划那条 policy，把根目录的临时 PDF 归位为 原件.pdf。"""
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT policy_id, title, local_path FROM policy WHERE title LIKE '%上虞%' AND title LIKE '%发展轴%'"
).fetchall()
if not rows:
    print("没有匹配的 policy，PDF 保留原处")
    raise SystemExit(0)

src = ROOT / "_tmp_sy_fazhanzhou.pdf"
for r in rows:
    dst = (ROOT / r["local_path"]).parent / "原件.pdf"
    print(f"{r['policy_id']} {r['title'][:56]}")
    print(f"   -> {dst.relative_to(ROOT)}")
    if src.exists():
        shutil.copy2(src, dst)
print("已归位" if src.exists() else "源文件不存在")
