"""一次性：核对 source_kind 枚举收敛 + raw 存档哈希一致性（ingest 后自检）。"""
import csv
import hashlib
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ("政策文件", "政府公报", "部门动态", "新闻发布")

conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

bad = conn.execute(
    "SELECT policy_id, source_kind FROM policy WHERE source_kind NOT IN (?,?,?,?)",
    CANON,
).fetchall()
print("非规范 source_kind:", len(bad))

print("\nsource_kind 分布:")
for r in conn.execute("SELECT source_kind, COUNT(*) n FROM policy GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  {r['source_kind']:<8} {r['n']}")

print("\npolicy 按省:")
for r in conn.execute(
    "SELECT province_code, COUNT(*) n FROM policy GROUP BY 1 ORDER BY 2 DESC LIMIT 8"
):
    print(f"  {r['province_code']} {r['n']}")

rows = conn.execute("SELECT policy_id, local_path, hash_sha256 FROM policy").fetchall()
missing, mismatch, empty = [], [], []
for r in rows:
    if not r["local_path"]:
        empty.append(r["policy_id"])
        continue
    p = ROOT / r["local_path"]
    if not p.exists():
        missing.append(r["policy_id"])
        continue
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != r["hash_sha256"]:
        mismatch.append(r["policy_id"])
print(f"\n存档核对：{len(rows)} 条 | 缺 local_path {len(empty)} | 文件缺失 {len(missing)} | 哈希不符 {len(mismatch)}")
if missing[:5]:
    print("  缺文件样例:", missing[:5])
if mismatch[:5]:
    print("  哈希不符样例:", mismatch[:5])
