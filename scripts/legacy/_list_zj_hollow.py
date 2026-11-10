"""列出浙江各分片的空心片区（有 area 记录但没有任何政策挂接），供补采派发排序。

注意：{shard}-counties.csv 的 area_ids 用 `|` 分隔（不是 `;`）。
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SH = ROOT / "data" / "stage" / "shards"

conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

linked = {r[0] for r in conn.execute("SELECT DISTINCT area_id FROM area_policy_map")}
areas = {
    r["area_id"]: r
    for r in conn.execute(
        "SELECT area_id, name, county_code FROM area "
        "WHERE province_code = '330000' AND record_state = 'active'"
    )
}
hollow = {a for a in areas if a not in linked}
print(f"浙江 active 片区 {len(areas)} / 已挂政策 {len(areas) - len(hollow)} / 空心 {len(hollow)}\n")


def ids_of(r: dict) -> list[str]:
    raw = r.get("area_ids") or ""
    for sep in ("|", ";"):
        if sep in raw:
            return [x.strip() for x in raw.split(sep) if x.strip()]
    return [raw.strip()] if raw.strip() else []


rows = []
for p in sorted(SH.glob("ZJ*-counties.csv")):
    shard = p.name.split("-")[0]
    recs = [r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if any(r.values())]
    ids = [i for r in recs for i in ids_of(r)]
    in_shard = [i for i in ids if i in areas]
    miss = [i for i in in_shard if i in hollow]
    rows.append((shard, len(recs), len(in_shard), len(miss)))

rows.sort(key=lambda x: -x[3])
print(f"{'分片':<6}{'县数':>5}{'片区数':>7}{'空心':>6}")
for s, nc, na, nm in rows:
    print(f"{s:<6}{nc:>5}{na:>7}{nm:>6}")
print(f"\n合计 片区 {sum(r[2] for r in rows)} / 空心 {sum(r[3] for r in rows)}")

print("\n空心最多的县：")
for r in conn.execute(
    """
    SELECT a.county_code, COUNT(*) n FROM area a
    WHERE a.province_code='330000' AND a.record_state='active'
      AND a.area_id NOT IN (SELECT area_id FROM area_policy_map)
    GROUP BY a.county_code ORDER BY n DESC LIMIT 10
    """
):
    print(f"  {r['county_code']}  {r['n']}")
