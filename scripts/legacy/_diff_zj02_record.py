"""精确比对：ZJ02 文件里那条与库内 P330303 的 url/title 是否逐字符相同。"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rec = None
for line in (ROOT / "data" / "stage" / "batches" / "POL-ZJ02-policy.jsonl").open(encoding="utf-8"):
    if not line.strip():
        continue
    r = json.loads(line)
    if "钱塘区强村公司" in (r.get("title") or ""):
        rec = r
        break

row = conn.execute("SELECT policy_id, title, url FROM policy WHERE policy_id = 'P330303'").fetchone()

for name in ("title", "url"):
    a, b = rec.get(name) or "", row[name] or ""
    print(f"{name}: 相同={a == b}  文件长={len(a)} 库长={len(b)}")
    if a != b:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                print(f"   第 {i} 位起不同: 文件{ord(x):#x}({x!r}) vs 库{ord(y):#x}({y!r})")
                break
        print("   文件尾:", repr(a[-25:]))
        print("   库尾  :", repr(b[-25:]))

# 检查库里所有钱塘 url
print("\n库内钱塘 url 前缀：", {r[0][:45] for r in conn.execute("SELECT url FROM policy WHERE url LIKE '%qiantang%'")})
