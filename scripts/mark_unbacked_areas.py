"""把「证据链只有媒体」的片区标为 status=待核，并在 summary 留痕。

依据：
  - CLAUDE.md 决策日志 2025-06：片区采用**证据制准入**（官方来源可核验）
  - docs/07 §3.2：官方媒体仅入 source，不入 policy
  - docs/01：`status=待核` 的记录统计报告默认排除

判据（三条同时满足才标记）：
  1. 在 area_policy_map 里没有任何 rel IN ('primary','support') 的政策
  2. first_source_id 指向的 source.url 不含 .gov.cn
  3. status 当前为「运行中」（已待核/已撤销的不动）

处置：
  - status: 运行中 → 待核
  - summary 追加标记「【证据待核】唯一来源为<发布者>，需补 .gov.cn 官方依据」
  - 不删记录、不改名、不碰 raw

用法：
  python scripts/mark_unbacked_areas.py --dry-run
  python scripts/mark_unbacked_areas.py
  python scripts/mark_unbacked_areas.py --upgrade --dry-run   # 补到官方依据的升回运行中
  python scripts/mark_unbacked_areas.py --upgrade
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BY_PROV = ROOT / "data" / "clean" / "by_province"
MARK = "【证据待核】"

PROV_ABBR = {
    "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
    "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
    "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
    "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
    "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
    "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
    "650000": "XJ",
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def upgrade(dry: bool) -> int:
    """把已补到 primary/support 官方依据的待核片区，status 升回「运行中」。

    只处理**本脚本标记过的**（summary 含 MARK）——它们的待核原因就是「唯一来源为媒体」，
    现在补到官方依据即解除。原本就在 待核 的记录原因各不相同（如名称待核），
    不能因为有了政策依据就自动升回。
    """
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT a.area_id, a.name, a.province_code
        FROM area a
        WHERE a.record_state='active' AND a.status='待核'
          AND a.summary LIKE ?
          AND EXISTS (SELECT 1 FROM area_policy_map m
                      WHERE m.area_id=a.area_id AND m.rel IN ('primary','support'))
    """, (f"%{MARK}%",)).fetchall()
    print(f"可升级（本脚本标记为待核、且已补到官方依据）：{len(rows)} 条")

    today = date.today().isoformat()
    cache: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    edited = 0
    for r in rows:
        abbr = PROV_ABBR.get(r["province_code"])
        if not abbr:
            continue
        if abbr not in cache:
            cache[abbr] = _read(BY_PROV / f"{abbr}-area.csv")
        cols, area_rows = cache[abbr]
        for x in area_rows:
            if x.get("area_id") != r["area_id"]:
                continue
            sm = x.get("summary") or ""
            if MARK in sm:
                head, _, tail = sm.partition(MARK)
                x["summary"] = head.rstrip("｜ ")
            x["status"] = "运行中"
            x["updated_at"] = today
            edited += 1
            print(f"  ↑ {r['area_id']} {r['name'][:26]}")

    if dry:
        print(f"\ndry-run：将升级 {edited} 条，未写盘")
        return 0
    for abbr, (cols, area_rows) in cache.items():
        _write(BY_PROV / f"{abbr}-area.csv", cols, area_rows)
    print(f"\n已升级 {edited} 条；接着跑：merge_by_province -> build_db -> validate_db")
    return 0


def main() -> int:
    dry = "--dry-run" in sys.argv
    if "--upgrade" in sys.argv:
        return upgrade(dry)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT a.area_id, a.name, a.province_code, a.status, a.summary, a.first_source_id,
               s.url, s.publisher, s.title
        FROM area a
        LEFT JOIN source s ON s.source_id = a.first_source_id
        WHERE a.record_state = 'active'
          AND a.status = '运行中'
          AND NOT EXISTS (
              SELECT 1 FROM area_policy_map m
              WHERE m.area_id = a.area_id AND m.rel IN ('primary','support')
          )
    """).fetchall()

    targets = [r for r in rows if ".gov.cn" not in (r["url"] or "") and (r["url"] or "")]
    skipped_no_src = [r for r in rows if not (r["url"] or "")]

    print(f"待核候选：{len(targets)} 个（无 first_source 的 {len(skipped_no_src)} 个不动）")
    by_prov = Counter(r["province_code"] for r in targets)
    for p, n in by_prov.most_common(8):
        print(f"    {PROV_ABBR.get(p, p)} {n}")

    today = date.today().isoformat()
    edited = 0
    cache: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for r in targets:
        abbr = PROV_ABBR.get(r["province_code"])
        if not abbr:
            print(f"  !! 省码无法映射：{r['area_id']}")
            continue
        if abbr not in cache:
            cache[abbr] = _read(BY_PROV / f"{abbr}-area.csv")
        cols, area_rows = cache[abbr]
        hit = [x for x in area_rows if x.get("area_id") == r["area_id"]]
        if not hit:
            continue
        for x in hit:
            if MARK in (x.get("summary") or ""):
                continue
            note = (f"{MARK}唯一来源为{r['publisher'] or r['url']}，"
                    f"依证据制准入（CLAUDE.md 2025-06）需补 .gov.cn 官方依据")
            base = (x.get("summary") or "").strip()
            x["summary"] = f"{base}｜{note}" if base else note
            x["status"] = "待核"
            x["updated_at"] = today
            edited += 1

    print(f"\n标记 {edited} 条")
    for r in targets[:8]:
        print(f"  {r['area_id']} {r['name'][:26]:<28} ← {r['publisher'] or r['url'][:30]}")
    if len(targets) > 8:
        print(f"  …… 另 {len(targets) - 8} 条")

    if dry:
        print("\ndry-run，未写盘")
        return 0
    for abbr, (cols, area_rows) in cache.items():
        _write(BY_PROV / f"{abbr}-area.csv", cols, area_rows)
    print("\n已写入 by_province；接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
