"""一次性：定位 XZ01 那条中央「十五五」规划建议记录。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

for r in conn.execute(
    "SELECT policy_id, title, url, local_path, credibility, doc_type, source_kind, created_by "
    "FROM policy WHERE province_code = '540000' ORDER BY policy_id"
):
    print(f"{r['policy_id']} [{r['credibility']}/{r['doc_type']}/{r['source_kind']}] {r['title'][:52]}")
    print(f"    {r['url'][:100]}")
