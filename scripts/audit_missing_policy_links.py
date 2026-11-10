"""反查：政策正文里点名了片区，但 area_policy_map 没挂上。

成因：ingest_policy.py 只按 JSONL 的 `areas` 字段建映射，采集端漏填或后续补录的记录
就会出现「正文有证据、映射为空」。这类漏挂无法靠重新采集补（url 会去重），只能用定点脚本补。

判据（宁严勿滥）：
  - 片区名去标点后长度 >= 4，避免「新联」「周垟」这类两字名在正文里误命中
  - 片区名出现在正文里，且该 policy 与该 area 尚未有映射
  - 片区与政策同省（跨省同名不算）

用法：
  python scripts/audit_missing_policy_links.py            # 列出候选
  python scripts/audit_missing_policy_links.py --csv reports/qa/missing-policy-links.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－]+")
MIN_NAME = 4


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    areas = [
        (r["area_id"], r["province_code"], r["name"], norm(r["name"]))
        for r in conn.execute(
            "SELECT area_id, province_code, name FROM area WHERE record_state = 'active'"
        )
    ]
    linked = {(r[0], r[1]) for r in conn.execute("SELECT area_id, policy_id FROM area_policy_map")}

    hits = []
    for p in conn.execute("SELECT policy_id, province_code, local_path, title FROM policy"):
        body = ROOT / p["local_path"]
        if not body.exists():
            continue
        text = norm(body.read_text(encoding="utf-8"))
        for area_id, prov, name, nname in areas:
            if prov != p["province_code"] or len(nname) < MIN_NAME:
                continue
            if (area_id, p["policy_id"]) in linked:
                continue
            if nname in text:
                hits.append({
                    "area_id": area_id,
                    "area_name": name,
                    "policy_id": p["policy_id"],
                    "policy_title": p["title"][:60],
                })

    out = ROOT / "reports" / "qa" / "missing-policy-links.csv"
    if "--csv" in sys.argv:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["area_id", "area_name", "policy_id", "policy_title"])
            w.writeheader()
            w.writerows(hits)
        print(f"{len(hits)} 条候选 -> {out.relative_to(ROOT)}")
        return 0

    print(f"候选 {len(hits)} 条（正文点名但未挂接）\n")
    by_area: dict[str, list[str]] = {}
    for h in hits:
        by_area.setdefault(f"{h['area_id']} {h['area_name']}", []).append(h["policy_id"])
    for k in sorted(by_area):
        print(f"  {k:<34} <- {' '.join(sorted(set(by_area[k])))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
