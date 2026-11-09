"""查 POL-ZJ02 里那条钱塘区强村公司文件为何未入库。"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

# 1) 文件里的原始记录
rec = None
for line in (ROOT / "data" / "stage" / "batches" / "POL-ZJ02-policy.jsonl").open(encoding="utf-8"):
    if not line.strip():
        continue
    r = json.loads(line)
    if "钱塘区强村公司" in (r.get("title") or ""):
        rec = r
        break
if not rec:
    print("文件里找不到该记录")
    raise SystemExit(0)

print("文件记录：")
for k in ("title", "doc_no", "issuer", "published_ymd", "url", "source_kind", "credibility"):
    print(f"  {k:14} = {rec.get(k)!r}")
print(f"  full_text 汉字 = {len(rec.get('full_text') or '')}")
print(f"  areas = {rec.get('areas')}")

# 2) 库里钱塘/强村公司相关记录
print("\n库内相关记录：")
for r in conn.execute(
    "SELECT policy_id, title, doc_no, issuer, url, province_code FROM policy "
    "WHERE title LIKE '%钱塘%' OR title LIKE '%强村公司%'"
):
    print(f"  {r['policy_id']} [{r['province_code']}] {r['title'][:56]}")
    print(f"       doc_no={r['doc_no']!r} url={r['url'][:80]}")
