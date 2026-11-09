"""核对 AH02/CQ02 批次文件的每条 url 是否都已在 policy 表里（防僵尸实例改写文件后留下未入库行）。"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
db_urls = {r[0] for r in conn.execute("SELECT url FROM policy") if r[0]}
db_titles = {r[0] for r in conn.execute("SELECT title FROM policy") if r[0]}

for shard in ("AH02", "CQ02"):
    p = ROOT / "data" / "stage" / "batches" / f"POL-{shard}-policy.jsonl"
    rows = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
    missing_url = [r.get("title", "")[:40] for r in rows if (r.get("url") or "") not in db_urls]
    missing_title = [r.get("title", "")[:40] for r in rows if (r.get("title") or "") not in db_titles]
    print(f"{shard}: 文件 {len(rows)} 条 | url 未入库 {len(missing_url)} | 标题未入库 {len(missing_title)}")
    for t in missing_title:
        print("    标题未入库:", t)
