# -*- coding: utf-8 -*-
"""建 `county_roster` 县级名单台账（data/clean/county_roster.csv）。

数据来源：`policy` 中 `issuer_level='county'` 且属**名单/认定/公布**类（排除规划、批复规划）。
字段与省/市台账同构：official_count 优先取 `policy.target_areas`；否则取已挂接条数并注明口径。
status：in_db>0 → matched；有名单文件但 0 挂接 → partial；名单对象非片区 → not_area。

先用 --dry-run 看会写多少行。
"""
from __future__ import annotations

import csv
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "data" / "clean" / "county_roster.csv"
LIST_KW = re.compile(r"名单|认定|公布")
EXCLUDE_KW = re.compile(r"规划|批后|控规|国土空间|征求意见|方案")
COLS = ["county_code", "county_name", "city_code", "province_code", "roster_name", "roster_scope",
        "policy_id", "official_count", "in_db_count", "count_basis", "status", "note", "updated_at"]


def main() -> int:
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    region = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    today = "2026-11-21"
    rows: dict[str, dict] = {}

    for p in con.execute("""select policy_id, county_code, city_code, province_code, title,
        issued_ymd, published_ymd, doc_type, target_areas from policy
        where issuer_level='county' and county_code is not null"""):
        title = p["title"] or ""
        if not LIST_KW.search(title) or EXCLUDE_KW.search(title):
            continue
        cc = p["county_code"]
        reg = region.get(cc, {})
        linked = con.execute("""select count(*) from area_policy_map where policy_id=?
                                and rel in ('primary','support')""", (p["policy_id"],)).fetchone()[0]
        official = p["target_areas"] or None
        basis = "名单条数" if official else ("已挂接条数" if linked else "")
        # 对象层级：村/乡镇层名单不是片区
        village_only = bool(re.search(r"村", title)) and not bool(re.search(r"片区", title))
        town_only = bool(re.search(r"乡镇|示范镇|示范乡", title)) and not bool(re.search(r"片区", title))
        status = "matched" if linked else "partial"
        if village_only or town_only:
            status = "not_area"
        note = f"县级{('名单' if '名单' in title else '认定/公布')}类文件；"
        note += f"官方数 {official}" if official else "未见官方总数"
        note += f"；库内挂接 {linked}"
        if linked and official and linked > official:
            status = "partial"
            note += "（挂接数>官方数，可能含分建或重复）"
        cur = rows.get(cc)
        if cur and (cur["in_db_count"] or 0) >= linked:
            continue
        rows[cc] = {
            "county_code": cc, "county_name": reg.get("name", ""),
            "city_code": p["city_code"] or reg.get("parent_code", ""),
            "province_code": p["province_code"] or cc[:2] + "0000",
            "roster_name": title[:120], "roster_scope": (p["issued_ymd"] or p["published_ymd"] or "")[:10],
            "policy_id": p["policy_id"],
            "official_count": official or "",
            "in_db_count": linked, "count_basis": basis, "status": status,
            "note": note[:300], "updated_at": today,
        }

    out = [rows[k] for k in sorted(rows)]
    print(f"county_roster: {len(out)} 县（matched {sum(1 for r in out if r['status']=='matched')}"
          f" / partial {sum(1 for r in out if r['status']=='partial')}）")
    if dry:
        print("dry-run，未写盘")
        for r in out[:5]:
            print("  ", r["county_code"], r["county_name"], r["roster_name"][:36], "n=", r["in_db_count"])
        return 0
    tmp = OUT.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(out)
    os.replace(tmp, OUT)
    print("写盘 ->", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
