"""政策层覆盖度报告：按省/市看政策收集进度。

不评价质量，只报事实：哪些县已有政策、哪些还没有、每县多少份。

用法：
  python scripts/policy_coverage.py
  python scripts/policy_coverage.py --csv reports/qa/policy-coverage.csv
  python scripts/policy_coverage.py --missing          # 只列尚未覆盖的县
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"


def main() -> int:
    args = sys.argv[1:]
    to_csv = ""
    if "--csv" in args:
        to_csv = args[args.index("--csv") + 1]
    only_missing = "--missing" in args

    if not DB.exists():
        print(f"DB 不存在: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 每县：片区数、政策数（县级直接发文）、通过挂接得到的政策数
    rows = cur.execute(
        """select a.province_code p, rp.name pname, a.county_code c, rc.name cname,
                  count(distinct a.area_id) n_area,
                  count(distinct case when p.issuer_level='county' then p.policy_id end) n_pol_own,
                  count(distinct m.policy_id) n_pol_link
           from area a
           left join region rp on rp.region_code = a.province_code
           left join region rc on rc.region_code = a.county_code
           left join area_policy_map m on m.area_id = a.area_id and m.entity_type='area'
           left join policy p on p.policy_id = m.policy_id
           where a.record_state='active'
           group by a.county_code
           order by a.province_code, n_area desc"""
    ).fetchall()

    by_prov: dict[tuple, dict] = defaultdict(
        lambda: {"n_cty": 0, "n_area": 0, "cty_covered": 0, "cty_own": 0, "n_pol": 0}
    )
    detail = []
    for r in rows:
        k = (r["p"], r["pname"] or r["p"])
        b = by_prov[k]
        b["n_cty"] += 1
        b["n_area"] += r["n_area"]
        if r["n_pol_link"]:
            b["cty_covered"] += 1
        if r["n_pol_own"]:
            b["cty_own"] += 1
        b["n_pol"] += r["n_pol_own"]
        detail.append(r)

    print(f"{'省份':12s}{'县':>4s}{'片区':>6s}{'有政策依据的县':>14s}{'有县级发文':>10s}{'县级政策':>8s}")
    print("-" * 60)
    t = {"n_cty": 0, "n_area": 0, "cty_covered": 0, "cty_own": 0, "n_pol": 0}
    for k in sorted(by_prov, key=lambda x: -by_prov[x]["n_area"]):
        b = by_prov[k]
        for f in t:
            t[f] += b[f]
        pct = b["cty_covered"] / b["n_cty"] * 100 if b["n_cty"] else 0
        print(f"{k[1][:12]:12s}{b['n_cty']:>4d}{b['n_area']:>6d}"
              f"{b['cty_covered']:>8d} ({pct:3.0f}%){b['cty_own']:>10d}{b['n_pol']:>8d}")
    print("-" * 60)
    pct = t["cty_covered"] / t["n_cty"] * 100 if t["n_cty"] else 0
    print(f"{'合计':12s}{t['n_cty']:>4d}{t['n_area']:>6d}"
          f"{t['cty_covered']:>8d} ({pct:3.0f}%){t['cty_own']:>10d}{t['n_pol']:>8d}")

    tot_pol = cur.execute("select count(*) from policy").fetchone()[0]
    tot_map = cur.execute("select count(*) from area_policy_map").fetchone()[0]
    covered_area = cur.execute(
        "select count(distinct area_id) from area_policy_map where entity_type='area'"
    ).fetchone()[0]
    print(f"\n全库政策 {tot_pol} 份，片区-政策挂接 {tot_map} 条，"
          f"有政策依据的片区 {covered_area}/{t['n_area']} "
          f"({covered_area / t['n_area'] * 100:.1f}%)")

    if only_missing:
        print("\n尚未覆盖的县：")
        for r in detail:
            if not r["n_pol_link"]:
                print(f"  {r['c']} {r['cname'] or '?'} ({r['n_area']} 片区)")

    if to_csv:
        out = ROOT / to_csv
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["province_code", "province", "county_code", "county",
                        "n_areas", "n_policy_own", "n_policy_linked"])
            for r in detail:
                w.writerow([r["p"], r["pname"], r["c"], r["cname"],
                            r["n_area"], r["n_pol_own"], r["n_pol_link"]])
        print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
