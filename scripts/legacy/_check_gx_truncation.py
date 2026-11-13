"""核实广西田园综合体试点名单在库内的 full_text 是否只存了前 8 条。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, title, local_path, full_text_chars, target_areas FROM policy "
    "WHERE province_code='450000' AND (title LIKE '%田园综合体%' OR title LIKE '%试点%')"
):
    body = ROOT / r["local_path"]
    text = body.read_text(encoding="utf-8") if body.exists() else ""
    # 数一下条目：以数字或"XX市"开头的枚举行
    items = re.findall(r"(?:^|\n)\s*[（(]?\d+[）).、]\s*\S", text)
    units = re.findall(r"田园综合体", text)
    print(f"{r['policy_id']}  {r['title'][:52]}")
    print(f"   汉字 {r['full_text_chars']}  target_areas={r['target_areas'] or '-'}")
    print(f"   正文出现「田园综合体」{len(units)} 次；编号条目 {len(items)} 个")
    print(f"   末尾 120 字：…{text[-120:].replace(chr(10), ' ')}")
    print()
