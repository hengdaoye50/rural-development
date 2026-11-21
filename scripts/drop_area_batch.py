# -*- coding: utf-8 -*-
"""按批次/清单整体下架片区（口径不符时用），raw 移入 archive 不删。

用法：
  python scripts/drop_area_batch.py --policy P430034 --reason "集中连片不是片区化" --dry-run
  python scripts/drop_area_batch.py --ids A430001,A430002 --reason "..."

做四件事：
  1. 从 by_province 的 area / area_policy_map / area_region_map / area_source_map 删除对应行
  2. 删除仅被这些片区引用的 source 行（避免悬空）
  3. raw 目录移到 archive/{YYYY-MM}/dropped-area/
  4. 打印计数；不碰 region / policy（policy 用 drop_policy.py 单独下架）

注意：master 由 merge_by_province 重建，**不要手改 master**。
"""
from __future__ import annotations

import csv
import os
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = ROOT / "data" / "db" / "片区库.sqlite3"
ARCH = ROOT / "archive" / date.today().strftime("%Y-%m") / "dropped-area"


def read(p):
    if not p.exists():
        return [], []
    with p.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p, hdr, rows):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    os.replace(tmp, p)


def main() -> int:
    dry = "--dry-run" in sys.argv
    policy = ""
    if "--policy" in sys.argv:
        policy = sys.argv[sys.argv.index("--policy") + 1]
    ids: set[str] = set()
    if "--ids" in sys.argv:
        ids = {x.strip() for x in sys.argv[sys.argv.index("--ids") + 1].split(",") if x.strip()}
    reason = "口径不符"
    if "--reason" in sys.argv:
        reason = sys.argv[sys.argv.index("--reason") + 1]

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if policy:
        ids |= {r["area_id"] for r in con.execute(
            "select area_id from area_policy_map where policy_id=?", (policy,))}
    if not ids:
        print("没有要下架的片区")
        return 1
    src_ids = {r["source_id"] for r in con.execute(
        f"select distinct source_id from area_source_map where area_id in ({','.join('?' * len(ids))})",
        tuple(ids))}
    print(f"下架 {len(ids)} 个片区，关联 source {len(src_ids)} 条｜原因：{reason}")
    if dry:
        for aid in sorted(ids)[:5]:
            print("  ~", aid)
        print("dry-run，未写盘")
        return 0

    removed = dict(area=0, map=0, region=0, source_map=0, source=0)
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        keep = [r for r in rows if r.get("area_id") not in ids]
        if len(keep) != len(rows):
            removed["area"] += len(rows) - len(keep)
            write(p, hdr, keep)
    for name, key, k in (("area_policy_map", "area_id", "map"), ("area_region_map", "area_id", "region"),
                          ("area_source_map", "area_id", "source_map")):
        for p in sorted(BP.glob(f"*-{name}.csv")):
            hdr, rows = read(p)
            keep = [r for r in rows if r.get(key) not in ids]
            if len(keep) != len(rows):
                removed[k] += len(rows) - len(keep)
                write(p, hdr, keep)
    # 只被这些片区引用的 source
    still = {r["source_id"] for r in con.execute("select source_id from area_source_map")}
    # 另含「source.area_id 直接指向被删片区」的行
    drop_src = (src_ids - still) | {r["source_id"] for r in con.execute(
        f"select source_id from source where area_id in ({','.join('?' * len(ids))})", tuple(ids))}
    for p in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(p)
        keep = [r for r in rows if r.get("source_id") not in drop_src]
        if len(keep) != len(rows):
            removed["source"] += len(rows) - len(keep)
            write(p, hdr, keep)

    ARCH.mkdir(parents=True, exist_ok=True)
    moved = 0
    if policy:
        pol = con.execute("select local_path from policy where policy_id=?", (policy,)).fetchone()
        if pol and pol["local_path"]:
            d = (ROOT / pol["local_path"]).parent
            if d.is_dir():
                shutil.move(str(d), str(ARCH / f"{policy}-{d.name}"))
                moved += 1
    print("删除行：", removed, "｜raw 归档目录", moved)
    (ARCH / "_dropped.log").open("a", encoding="utf-8").write(
        f"{date.today()} policy={policy} ids={len(ids)} reason={reason}\n")
    print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
