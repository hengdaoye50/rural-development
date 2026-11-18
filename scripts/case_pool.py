"""案例池口径：从主统计里筛出「能写成案例」的片区，并导出清单。

为什么需要单独一层：`主统计 446` 只保证「可归时 + 有依据」，但写案例还要有**内容**——
范围、规模、时间精度、机制线索。四要素取三即入池，留一档容错。

四要素（都可回原文核）：
- cover_ok：`cover_desc` 有效（≥20 字，且不等于名称）
- scale_ok：有 `scale_villages` 或 `scale_towns`
- event_ok：至少 1 条 `event`（设立/入选/批复等）
- date_ok：`founded_precision` 为 day 或 month

分层：A ≥3 要素（案例池）/ B =2（简案）/ C ≤1（仅附表）/ D 时间不详或口径外 / E 无依据。

    python scripts/case_pool.py            # 打印分层与结构
    python scripts/case_pool.py --csv reports/qa/case-pool.csv
"""
from __future__ import annotations

import csv
import collections
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"


def main(argv: list[str]) -> int:
    out_csv = ROOT / argv[argv.index("--csv") + 1] if "--csv" in argv else None
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = list(con.execute("""
        select a.area_id, a.name, a.province_code, a.county_code, a.setup_kind,
               a.cover_desc, a.founded_ymd, a.founded_precision,
               a.scale_villages, a.scale_towns,
               (select count(*) from area_policy_map m
                 where m.area_id=a.area_id and m.rel in ('primary','support')) hard,
               (select count(*) from event e where e.area_id=a.area_id) nev,
               (select count(*) from area_caliber x
                 where x.area_id=a.area_id and x.in_main_stat=1) main
        from area a
        where a.record_state='active' and a.status<>'待核'"""))

    def cover_ok(r):
        cd = (r["cover_desc"] or "").strip().rstrip("。")
        return len(cd) >= 20 and cd != (r["name"] or "").strip()

    def scale_ok(r):
        return bool(str(r["scale_villages"] or "").strip() or str(r["scale_towns"] or "").strip())

    tiers = collections.Counter()
    pool = []
    for r in rows:
        if r["hard"] == 0:
            tiers["E 无依据"] += 1
            continue
        if not r["main"]:
            tiers["D 时间不详或口径外"] += 1
            continue
        flags = {
            "cover_ok": int(cover_ok(r)),
            "scale_ok": int(scale_ok(r)),
            "event_ok": int(r["nev"] > 0),
            "date_ok": int(r["founded_precision"] in ("day", "month")),
        }
        score = sum(flags.values())
        tiers["A 案例池（>=3）" if score >= 3 else
              "B 简案（=2）" if score == 2 else "C 仅附表（<=1）"] += 1
        if score >= 3:
            pool.append({**{k: r[k] for k in (
                "area_id", "name", "province_code", "county_code", "setup_kind",
                "founded_ymd", "scale_villages", "scale_towns")},
                **flags, "score": score, "n_hard": r["hard"], "n_event": r["nev"]})

    print("=== 案例可用性分层（在册非待核 %d 条）===" % len(rows))
    for k in sorted(tiers):
        print("  %s: %d" % (k, tiers[k]))
    print("\nA 档合计 %d" % len(pool))
    prov = {r["region_code"]: (r["short_name"] or r["name"]) for r in con.execute(
        "select region_code,name,short_name from region where level='province'")}
    print("分省:", "、".join(f"{prov.get(p,p)} {n}" for p, n in
                             collections.Counter(r["province_code"] for r in pool).most_common(8)))
    print("setup_kind:", dict(collections.Counter(r["setup_kind"] for r in pool)))

    if out_csv:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(pool[0].keys()))
            w.writeheader()
            w.writerows(pool)
        print(f"清单 -> {out_csv.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
