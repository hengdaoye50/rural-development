"""一次性：用 OCR 首页文本给未归档扫描件定位归属 policy。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tmp" / "ocrprobe"

conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

policies = conn.execute("SELECT policy_id, local_path, title FROM policy").fetchall()

for f in sorted(PROBE.glob("*.txt")):
    txt = f.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"<!--.*?-->", "", txt)
    flat = re.sub(r"\s+", "", txt)
    print(f"=== {f.stem} ===")
    print("  首页：", flat[:70])
    keys = [k for k in re.findall(r"[\u4e00-\u9fa5]{4,}", flat[:120])]
    hits = []
    for p in policies:
        t = re.sub(r"\s+", "", p["title"])
        score = sum(1 for k in keys if k in t)
        if score >= 3:
            hits.append((score, p["policy_id"], p["title"][:60], p["local_path"]))
    hits.sort(reverse=True)
    if hits:
        for h in hits[:3]:
            print(f"    候选 {h[0]}分  {h[1]}  {h[2]}")
            print(f"            {h[3]}")
    else:
        print("    库内无匹配（可能未入库）")
    print()
