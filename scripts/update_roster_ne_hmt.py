# -*- coding: utf-8 -*-
"""给 province_roster 增加「资料暂缺」状态，并补写东北三省与港澳台台账（一次性）。

- 状态枚举新增 unavailable（资料暂缺）：港澳台不纳入采集，不挂零，显式标注
- 东北三省：按 2026 年新政策改写台账（吉林 66 个省级试点片区；黑龙江首批试点；辽宁示范带以 belt 记录）
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLS = ["province_code", "roster_name", "roster_scope", "policy_id", "source_id",
        "official_count", "in_db_count", "count_basis", "status", "note", "updated_at"]
NOW = datetime.now().astimezone().isoformat(timespec="seconds")

UPDATES = {
    "220000": dict(roster_name="省级试点片区", roster_scope="2026 首批",
                   official_count="66", in_db_count="4", count_basis="官方数量",
                   status="count_only",
                   note="2026 年启动 66 个省级试点片区（种植29/养殖7/文旅30，覆盖385村，"
                        "每县先确定1个）；逐条名单未公开，已按报道点名入库 4 条待核"),
    "230000": dict(roster_name="片区化乡村振兴试点", roster_scope="首批",
                   official_count="", in_db_count="1", count_basis="试点名单",
                   status="count_only",
                   note="黑龙江「十五五」规划部署探索片区化试点；首批名单未逐条公开，"
                        "已按报道点名入库桦川县 1 条待核"),
    "210000": dict(status="partial",
                   note="2023 省级乡村振兴示范带 23 条（按口径迁入 belt，不计 area）；"
                        "另有沈阳等市县级乡村振兴片区，逐条名单需进一步采集"),
    "810000": dict(roster_name="资料暂缺", roster_scope="", policy_id="", source_id="",
                   official_count="", in_db_count="0", count_basis="不纳入采集",
                   status="unavailable", note="香港特别行政区：按研究范围不纳入采集，资料暂缺"),
    "820000": dict(roster_name="资料暂缺", roster_scope="", policy_id="", source_id="",
                   official_count="", in_db_count="0", count_basis="不纳入采集",
                   status="unavailable", note="澳门特别行政区：按研究范围不纳入采集，资料暂缺"),
    "710000": dict(roster_name="资料暂缺", roster_scope="", policy_id="", source_id="",
                   official_count="", in_db_count="0", count_basis="不纳入采集",
                   status="unavailable", note="台湾省：按研究范围不纳入采集，资料暂缺"),
}


def read(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
    for r in rows:
        assert set(r) <= set(hdr), f"{p.name}: {set(r) - set(hdr)}"
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(p)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = ROOT / "data" / "clean" / "province_roster.csv"
    hdr, rows = read(p)
    by = {r["province_code"]: r for r in rows}
    for code, upd in UPDATES.items():
        r = by.get(code)
        if r is None:
            r = {k: "" for k in hdr}
            r["province_code"] = code
            rows.append(r)
            by[code] = r
        r.update(upd)
        r["updated_at"] = NOW
        print(f"  {code} {r['status']} {r['roster_name']}")
    write(p, hdr, rows)
    print("province_roster 更新完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
