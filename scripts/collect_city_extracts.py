"""把 agent 落盘的 `city-extract-{code}.json` 转成 `apply_city_roster_scan` 可用的扫描 JSON。

规则：
  - 跳过 `*-pending.json`（只有第三方转载的待激活名单）
  - 跳过 `ok=false` 或无 areas 的
  - 跳过台账里**已有名单信息**的城市（避免覆盖人工核定过的 matched/note）
  - 其余：official_count=areas 数，status=partial（名单已定位待入库），source_kind 按域名判 gov/media

用法：
  python scripts/collect_city_extracts.py --out data/stage/candidates/city-scan-from-extracts.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data" / "stage" / "candidates"
CSV = ROOT / "data" / "clean" / "city_roster.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(CAND / "city-scan-from-extracts.json"))
    args = ap.parse_args()

    existing = {}
    if CSV.exists():
        with CSV.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                existing[r["city_code"]] = r

    cities, skipped = [], []
    for p in sorted(CAND.glob("city-extract-*.json")):
        if p.stem.endswith("-pending"):
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            skipped.append(f"{p.name}: JSON 解析失败 {e}")
            continue
        code = str(d.get("city_code") or p.stem.split("-")[-1])
        areas = d.get("areas") or []
        if not d.get("ok") or not areas:
            skipped.append(f"{code}: ok=false 或无 areas")
            continue
        cur = existing.get(code) or {}
        if (cur.get("roster_name") or "").strip():
            skipped.append(f"{code}: 台账已有名单信息，跳过")
            continue
        url = (d.get("policy_url") or "").strip()
        cities.append({
            "city_code": code, "city_name": d.get("city_name") or p.stem, "found": True,
            "roster_name": (d.get("policy_title") or "市级片区名单")[:120],
            "roster_scope": (d.get("policy_published_ymd") or "")[:60],
            "source_url": url,
            "source_kind": "gov" if ".gov.cn" in url else "media",
            "count_int": len(areas), "count_basis": "名单条数",
            "names_listed": True, "county_mapping_available": True,
            "status_suggestion": "partial",
            "evidence_excerpt": "",
            "note": ((d.get("problem") or "")[:120] + f"；已从官方页抽取 {len(areas)} 条待入库")[:300],
            "confidence": "medium",
        })
    out = Path(args.out)
    out.write_text(json.dumps({"cities": cities}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"收集 {len(cities)} 市 -> {out}")
    for s in skipped[:12]:
        print("  -", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
