"""列出指定省份各分片的空心片区（有 area 记录但无任何政策挂接），按缺口排序。

用法：
  python scripts/legacy/_list_prov_hollow.py SD          # 山东
  python scripts/legacy/_list_prov_hollow.py ZJ --ids    # 同时输出 area_id 清单
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SH = ROOT / "data" / "stage" / "shards"
PROV_CODE = {
    "BJ": "110000", "TJ": "120000", "HE": "130000", "SX": "140000", "NM": "150000",
    "LN": "210000", "JL": "220000", "HL": "230000", "SH": "310000", "JS": "320000",
    "ZJ": "330000", "AH": "340000", "FJ": "350000", "JX": "360000", "SD": "370000",
    "HA": "410000", "HB": "420000", "HN": "430000", "GD": "440000", "GX": "450000",
    "HI": "460000", "CQ": "500000", "SC": "510000", "GZ": "520000", "YN": "530000",
    "XZ": "540000", "SN": "610000", "GS": "620000", "QH": "630000", "NX": "640000",
    "XJ": "650000",
}


def ids_of(r: dict) -> list[str]:
    raw = r.get("area_ids") or ""
    for sep in ("|", ";"):
        if sep in raw:
            return [x.strip() for x in raw.split(sep) if x.strip()]
    return [raw.strip()] if raw.strip() else []


def main() -> int:
    abbr = (sys.argv[1] if len(sys.argv) > 1 else "SD").upper()
    want_ids = "--ids" in sys.argv
    code = PROV_CODE[abbr]

    conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
    conn.row_factory = sqlite3.Row
    linked = {r[0] for r in conn.execute("SELECT DISTINCT area_id FROM area_policy_map")}
    active = {
        r[0]
        for r in conn.execute(
            "SELECT area_id FROM area WHERE province_code=? AND record_state='active'", (code,)
        )
    }
    hollow = active - linked
    print(f"{abbr} active 片区 {len(active)} / 已挂 {len(active) - len(hollow)} / 空心 {len(hollow)}\n")

    out = []
    for p in sorted(SH.glob(f"{abbr}*-counties.csv")):
        shard = p.name.split("-")[0]
        with p.open(encoding="utf-8-sig") as f:
            recs = [r for r in csv.DictReader(f) if any(r.values())]
        ids = [i for r in recs for i in ids_of(r)]
        in_shard = [i for i in ids if i in active]
        miss = [i for i in in_shard if i in hollow]
        out.append((shard, len(recs), len(in_shard), miss))

    out.sort(key=lambda x: -len(x[3]))
    print(f"{'分片':<7}{'县数':>5}{'片区':>6}{'空心':>6}")
    for shard, nc, na, miss in out:
        print(f"{shard:<7}{nc:>5}{na:>6}{len(miss):>6}")
    print(f"\n合计 片区 {sum(o[2] for o in out)} / 空心 {sum(len(o[3]) for o in out)}")

    if want_ids:
        print()
        for shard, _nc, _na, miss in out:
            if miss:
                print(f"{shard} ({len(miss)}): {' '.join(miss)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
