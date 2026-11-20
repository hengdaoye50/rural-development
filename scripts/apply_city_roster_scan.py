"""把市級名单扫描结果（workflow JSON）合并进 `data/clean/city_roster.csv`。

输入：`data/stage/candidates/city-roster-scan-{date}.json`，结构：
  {"cities":[{city_code, city_name, found, roster_name, roster_scope, source_url,
              source_kind, count_int, count_basis, names_listed,
              county_mapping_available, status_suggestion, evidence_excerpt, note,
              confidence}, ...], "specials":[...]}

规则（防编造）：
  - found=false 或 source_kind=none → 不改该市（保持现状）
  - source_kind=gov 且 names_listed=false → 最多记 partial/count_only
  - 任何写入都要求 source_url 非空且以 http 开头
  - official_count 只在 count_int>0 时写
  - status 直接采用 status_suggestion（枚举已校验）
  - note 拼上「扫描日期 + 置信度 + 摘录来源」，保留人工 note 里的探测记录

用法：
  python scripts/apply_city_roster_scan.py data/stage/candidates/city-roster-scan-2026-11-21.json --dry-run
  python scripts/apply_city_roster_scan.py <json>
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "clean" / "city_roster.csv"
STATUS = {"matched", "partial", "count_only", "not_area", "none"}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    cities = payload.get("cities") or []
    rows = list(csv.DictReader(CSV.open(encoding="utf-8-sig", newline="")))
    hdr = list(rows[0].keys())
    by_code = {r["city_code"]: r for r in rows}

    changes, skipped = [], []
    for c in cities:
        code = (c.get("city_code") or "").strip()
        r = by_code.get(code)
        if not r:
            skipped.append(f"{code or '?'} 不在台账（非浙苏鲁？）")
            continue
        if not c.get("found") or (c.get("source_kind") or "none") == "none":
            skipped.append(f"{code} {c.get('city_name')}: 未找到官方名单")
            continue
        url = (c.get("source_url") or "").strip()
        st = (c.get("status_suggestion") or "").strip()
        if not url.startswith("http") or st not in STATUS:
            skipped.append(f"{code}: 字段不合法（url/status）")
            continue
        if st == "matched" and not c.get("names_listed"):
            st = "partial"  # 没有逐条名单不能记已对账
        cur_in_db = int((r.get("in_db_count") or "0") or 0)
        if r.get("status") == "matched" and cur_in_db > 0:
            st = "matched"  # 已对账的不因扫描结论降级
        elif st == "matched" and cur_in_db == 0:
            st = "partial"  # 名单找到但条目还没入库：只能算待入库
        cnt = int(c.get("count_int") or 0)
        excerpt = (c.get("evidence_excerpt") or "").strip()
        note = (c.get("note") or "").strip()
        tail = f"[扫描 {date.today().isoformat()}｜{c.get('confidence') or '?'}]"
        tail += f" 来源：{url}"
        if excerpt:
            tail += f"｜原文：{excerpt[:100]}"
        changes.append((r, dict(
            roster_name=(c.get("roster_name") or r["roster_name"])[:120],
            roster_scope=(c.get("roster_scope") or r["roster_scope"])[:120],
            official_count=str(cnt) if cnt > 0 else r["official_count"],
            count_basis=(c.get("count_basis") or r["count_basis"]),
            status=st,
            note=" ".join(x for x in [note, r["note"], tail] if x)[:600],
        )))

    print(f"扫描 {len(cities)} 市：可更新 {len(changes)}，跳过 {len(skipped)}")
    for r, u in changes:
        print(f"  {r['city_code']} {r['city_name']}: {r['status']} -> {u['status']} | "
              f"{u['roster_name'][:40]} | 数={u['official_count'] or '—'}")
    for s in skipped[:10]:
        print("  -", s)
    if dry:
        print("dry-run，未写盘")
        return 0
    for r, u in changes:
        r.update(u)
        r["updated_at"] = date.today().isoformat() + "T00:00:00+08:00"
    with CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print(f"已写 {CSV.relative_to(ROOT)}")
    print("接着跑：build_db -> validate_db -> report_city_roster -> check_doc_caliber")
    return 0


if __name__ == "__main__":
    sys.exit(main())
