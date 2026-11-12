"""查看 source 表结构与辽宁现状，供名单补建时派生来源。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

print("source 列:", [r[1] for r in conn.execute("PRAGMA table_info(source)")])
print("\n辽宁 source 样例：")
for r in conn.execute(
    "SELECT source_id, area_id, publisher, credibility, published_ymd, substr(url,1,50) u "
    "FROM source WHERE source_id LIKE 'S21%' LIMIT 6"
):
    print(" ", dict(r))
n = conn.execute("SELECT COUNT(*) FROM source WHERE source_id LIKE 'S21%'").fetchone()[0]
print(f"\n辽宁 source 行数 {n}")

print("\nP210001 可用于派生来源的字段：")
r = conn.execute(
    "SELECT policy_id, title, issuer, published_ymd, issued_ymd, url, local_path, hash_sha256, "
    "credibility FROM policy WHERE policy_id='P210001'"
).fetchone()
print(" ", dict(r))
