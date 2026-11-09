"""全量核对：所有 POL-*.jsonl 的每条记录是否都已在 policy 表里。

僵尸子代理可能在被取消后又恢复执行并改写批次文件，导致 stage 与库不一致。
判据按 ingest_policy.py 的三条去重规则对应判定「已入库」：
  1. url 命中
  2. title（去标点）命中
  3. doc_no + issuer 命中（同一份文件在另一栏目转载时走这条）

显式放行：POL-XZ01 里那条中共中央「十五五」规划建议是按口径主动剔除的，不算缺口。
"""
import glob
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-]+")

INTENTIONAL_DROP = {"中共中央关于制定国民经济和社会发展第十五个五年规划的建议"}

conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
db_urls, db_titles, db_docs = set(), set(), set()
for title, url, doc_no, issuer in conn.execute(
    "SELECT title, url, doc_no, issuer FROM policy"
):
    if url:
        db_urls.add(url)
    if title:
        db_titles.add(PUNCT.sub("", title))
    if doc_no:
        db_docs.add((doc_no.strip(), (issuer or "").strip()))


def ingested(r: dict) -> bool:
    if (r.get("url") or "") in db_urls:
        return True
    if PUNCT.sub("", r.get("title") or "") in db_titles:
        return True
    doc = (r.get("doc_no") or "").strip()
    return bool(doc) and (doc, (r.get("issuer") or "").strip()) in db_docs


total, dropped, bad = 0, 0, []
for p in sorted(glob.glob(str(ROOT / "data" / "stage" / "batches" / "POL-*.jsonl"))):
    path = Path(p)
    with path.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    total += len(rows)
    miss = []
    for r in rows:
        if ingested(r):
            continue
        if (r.get("title") or "") in INTENTIONAL_DROP:
            dropped += 1
            continue
        miss.append(r)
    if miss:
        bad.append((path.name, len(rows), miss))

print(f"批次文件记录总数（含重复与主动剔除） {total}")
print(f"其中主动剔除 {dropped} 条")
if not bad:
    print("其余全部已入库：stage 与 policy 表一致，无遗留未入库产出。")
else:
    print(f"!! {len(bad)} 个批次存在未入库记录：")
    for name, n, miss in bad:
        print(f"  {name}: {n} 行 / 未入库 {len(miss)}")
        for m in miss[:5]:
            print("      ", (m.get("title") or "")[:50], "|", (m.get("url") or "")[:60])
