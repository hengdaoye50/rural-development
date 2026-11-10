"""输出每个浙江分片的空心 area_id 清单（空格分隔，便于直接塞进派发简报）。"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SH = ROOT / "data" / "stage" / "shards"

conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

linked = {r[0] for r in conn.execute("SELECT DISTINCT area_id FROM area_policy_map")}
active = {
    r[0]
    for r in conn.execute(
        "SELECT area_id FROM area WHERE province_code='330000' AND record_state='active'"
    )
}
hollow = active - linked


def ids_of(r: dict) -> list[str]:
    raw = r.get("area_ids") or ""
    for sep in ("|", ";"):
        if sep in raw:
            return [x.strip() for x in raw.split(sep) if x.strip()]
    return [raw.strip()] if raw.strip() else []


for p in sorted(SH.glob("ZJ*-counties.csv")):
    shard = p.name.split("-")[0]
    recs = [r for r in csv.DictReader(p.open(encoding="utf-8-sig")) if any(r.values())]
    ids = [i for r in recs for i in ids_of(r)]
    miss = [i for i in ids if i in hollow]
    if not miss:
        continue
    print(f"{shard} ({len(miss)}): {' '.join(miss)}")
