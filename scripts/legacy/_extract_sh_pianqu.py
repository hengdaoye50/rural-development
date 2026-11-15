"""从 P310023 里抽出所有「XX产业片区」条目，与空心片区对账。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

r = conn.execute("SELECT local_path FROM policy WHERE policy_id='P310023'").fetchone()
text = (ROOT / r["local_path"]).read_text(encoding="utf-8")

print("=== P310023 中出现的「产业片区」条目 ===")
for m in re.finditer(r"（[一二三四五六七八九十]+）([^\n。]{4,40}?产业片区)", text):
    print(f"  {m.group(1)}")

print("\n=== 上海现有片区中仍空心的 ===")
for a in conn.execute(
    """
    SELECT area_id, name FROM area
    WHERE province_code='310000' AND record_state='active'
      AND NOT EXISTS (SELECT 1 FROM area_policy_map m WHERE m.area_id=area.area_id)
    """
):
    print(f"  {a['area_id']} {a['name']}")
