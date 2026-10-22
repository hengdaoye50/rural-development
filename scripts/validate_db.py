"""校验 clean CSV / SQLite：必填、枚举、引用完整性、重复名、来源完备。"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT_DIR = ROOT / "reports" / "qa"

TYPE_CODES = {"T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"}
STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
RECORD_STATE = {"active", "superseded", "withdrawn"}
PRECISION = {"day", "month", "year", "unknown"}
CRED = {"A", "B", "C", "D", "E"}
BELT_TYPES = {"带", "圈", "廊", "片", "走廊", "环", "线", "其他"}
BELT_ROLE = {"county", "town", "village", "spine", "node"}

BELT_REQUIRED = [
    "belt_id", "name", "name_norm", "belt_type", "province_code", "city_code",
    "cover_desc", "year_precision", "record_state",
    "created_at", "updated_at", "created_by",
]

AREA_REQUIRED = [
    "area_id", "name", "name_norm", "type_code", "province_code", "city_code",
    "county_code", "cover_desc", "founded_precision", "status", "record_state",
    "created_at", "updated_at", "created_by",
]


def _rows(name: str) -> list[dict[str, str]]:
    p = CLEAN / name
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate() -> int:
    issues: list[str] = []
    warnings: list[str] = []
    areas = _rows("area.csv")
    sources = _rows("source.csv")
    regions = _rows("region.csv")
    belts = _rows("belt.csv")

    area_ids = {a["area_id"] for a in areas}
    belt_ids = {b["belt_id"] for b in belts}
    region_ids = {r["region_code"] for r in regions}

    for a in areas:
        aid = a.get("area_id") or "<empty>"
        for k in AREA_REQUIRED:
            if not a.get(k):
                issues.append(f"[area:{aid}] 缺必填字段 {k}")
        if a.get("type_code") not in TYPE_CODES:
            issues.append(f"[area:{aid}] 非法 type_code={a.get('type_code')}")
        if a.get("status") not in STATUS:
            issues.append(f"[area:{aid}] 非法 status={a.get('status')}")
        if a.get("record_state") not in RECORD_STATE:
            issues.append(f"[area:{aid}] 非法 record_state={a.get('record_state')}")
        if a.get("founded_precision") not in PRECISION:
            issues.append(f"[area:{aid}] 非法 founded_precision={a.get('founded_precision')}")

    # duplicate active name_norm in same county
    keys = [
        (a["county_code"], a["name_norm"])
        for a in areas
        if a.get("record_state") == "active"
    ]
    for key, n in Counter(keys).items():
        if n > 1:
            issues.append(f"[area] active 重复 name_norm+county: {key} x{n}")

    for s in sources:
        sid = s.get("source_id") or "<empty>"
        for k in ("source_id", "area_id", "url", "title", "publisher", "excerpt", "fetched_at", "credibility"):
            if not s.get(k):
                issues.append(f"[source:{sid}] 缺必填字段 {k}")
        if s.get("credibility") not in CRED:
            issues.append(f"[source:{sid}] 非法 credibility={s.get('credibility')}")
        ref = s.get("area_id") or ""
        if ref and ref not in area_ids and ref not in belt_ids:
            issues.append(f"[source:{sid}] area_id 既非 area 也非 belt: {ref}")
        if s.get("credibility") in {"A", "B", "C"} and not s.get("local_path"):
            warnings.append(f"[source:{sid}] A/B/C 级缺 local_path 快照")
        if s.get("excerpt") and len(s["excerpt"]) < 40:
            issues.append(f"[source:{sid}] excerpt 过短 (<40字)")

    source_by_id = {s.get("source_id"): s for s in sources}
    source_primary = {s.get("area_id") for s in sources}

    for a in areas:
        aid = a["area_id"]
        sid = a.get("first_source_id") or ""
        linked = (aid in source_primary) or (sid in source_by_id)
        if not linked:
            if a.get("status") != "待核":
                issues.append(f"[area:{aid}] 无任何 source（且 status≠待核）")

    if regions:
        for r in regions:
            if not r.get("region_code") or not r.get("name") or not r.get("level"):
                issues.append(f"[region] 缺字段: {r}")
    else:
        issues.append("[region] region.csv 为空（试点期至少应有省级）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_ids = {s.get("source_id") for s in sources}

    for b in belts:
        bid = b.get("belt_id") or "<empty>"
        for k in BELT_REQUIRED:
            if not b.get(k):
                issues.append(f"[belt:{bid}] 缺必填字段 {k}")
        if b.get("belt_type") not in BELT_TYPES:
            issues.append(f"[belt:{bid}] 非法 belt_type={b.get('belt_type')}")
        if b.get("record_state") not in RECORD_STATE:
            issues.append(f"[belt:{bid}] 非法 record_state={b.get('record_state')}")
        if b.get("year_precision") not in PRECISION:
            issues.append(f"[belt:{bid}] 非法 year_precision={b.get('year_precision')}")
        if b.get("source_id") and b["source_id"] not in source_ids:
            issues.append(f"[belt:{bid}] source_id 不存在: {b['source_id']}")

    bkeys = [
        (b["province_code"], b["name_norm"], b["belt_type"])
        for b in belts
        if b.get("record_state") == "active"
    ]
    for key, n in Counter(bkeys).items():
        if n > 1:
            issues.append(f"[belt] active 重复 key: {key} x{n}")

    out = OUT_DIR / "validate-latest.md"
    lines = [
        "# QA 报告",
        "",
        f"- area: {len(areas)}",
        f"- source: {len(sources)}",
        f"- region: {len(regions)}",
        f"- belt: {len(belts)}",
        f"- issues: {len(issues)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if issues:
        lines.append("## 问题清单")
        lines.extend(f"- {i}" for i in issues)
    else:
        lines.append("问题清单为空。")
    if warnings:
        lines.append("")
        lines.append("## 警告（不阻断）")
        lines.extend(f"- {w}" for w in warnings)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"issues={len(issues)} warnings={len(warnings)} -> {out}")
    for i in issues[:20]:
        print(" -", i)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(validate())
