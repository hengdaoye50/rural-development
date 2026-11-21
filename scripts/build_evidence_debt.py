# -*- coding: utf-8 -*-
"""建 `evidence_debt` 证据欠账表（data/clean/evidence_debt.csv）。

把审计 WARN 变成可跟踪任务单。债务类型：
  excerpt_digest   source.excerpt_status='digest'（导航性摘要，非逐字）
  missing_snapshot source 无 local_path（含死链）
  no_primary       在册非待核但无 primary/support 依据（E 组）
  pending_review   status=待核（证据链待补）
  county_village   县级名单对象是村/乡镇层（county_roster.not_area）

用法：python scripts/build_evidence_debt.py [--dry-run]
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "data" / "clean" / "evidence_debt.csv"
COLS = ["debt_id", "entity_type", "entity_id", "entity_name", "province_code",
        "debt_type", "actionable", "detail", "last_seen"]
ACTIONABLE = {"excerpt_digest", "missing_snapshot"}
TODAY = "2026-11-21"


def main() -> int:
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows: list[dict] = []

    def add(entity_type, eid, name, prov, dtype, detail):
        rows.append(dict(debt_id=f"{dtype}:{eid}", entity_type=entity_type, entity_id=eid,
                         entity_name=(name or "")[:60], province_code=prov or "",
                         debt_type=dtype, actionable=1 if dtype in ACTIONABLE else 0,
                         detail=(detail or "")[:160], last_seen=TODAY))

    for s in con.execute("select source_id, title, excerpt_status, local_path from source"):
        if s["excerpt_status"] == "digest":
            add("source", s["source_id"], s["title"], "", "excerpt_digest", "摘录为导航性摘要，非快照逐字")
        elif s["excerpt_status"] in ("missing", None) or (s["excerpt_status"] == "missing"):
            add("source", s["source_id"], s["title"], "", "missing_snapshot", "无本地快照（死链或未抓）")

    for a in con.execute("""select a.area_id, a.name, a.province_code, a.status,
        (select count(*) from area_policy_map m where m.area_id=a.area_id and m.rel in ('primary','support')) n
        from area a where a.record_state='active'"""):
        if a["status"] == "待核":
            add("area", a["area_id"], a["name"], a["province_code"], "pending_review", "status=待核")
        elif a["n"] == 0:
            add("area", a["area_id"], a["name"], a["province_code"], "no_primary", "无 primary/support 依据（E 组）")

    if (ROOT / "data" / "clean" / "county_roster.csv").exists():
        with (ROOT / "data" / "clean" / "county_roster.csv").open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["status"] == "not_area":
                    add("county_roster", r["county_code"], r["county_name"], r["province_code"],
                        "county_village", r["roster_name"][:80])

    cnt = Counter(r["debt_type"] for r in rows)
    act = sum(1 for r in rows if r["actionable"])
    print("evidence_debt:", len(rows), dict(cnt), f"其中可执行 {act} / 结构性 {len(rows) - act}")
    if dry:
        print("dry-run，未写盘")
        return 0
    tmp = OUT.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, OUT)
    print("写盘 ->", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
