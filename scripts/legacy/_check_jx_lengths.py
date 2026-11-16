"""检查江西试点两批报告的全文长度，识别「摘要」而非全文的记录。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

for batch in ("JX-PILOT", "JX-PILOT2"):
    p = ROOT / "data" / "stage" / "batches" / f"POL-{batch}-policy.jsonl"
    if not p.exists():
        continue
    print(f"=== {batch} ===")
    for line in p.open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        n = len(r.get("full_text") or "")
        mark = "  <== 疑摘要/过短" if n < 6000 else ""
        print(f"  {r.get('county_code')} {n:>6} 字  {(r.get('title') or '')[:36]}{mark}")
