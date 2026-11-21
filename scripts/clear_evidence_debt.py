# -*- coding: utf-8 -*-
"""清欠账 A 组：mention→support（正文点名）、credibility C→B（.gov.cn 域名）、待核→运行中（有 gov 来源）。

规则依据：
  - mention 只是「提到」，若政策全文/标题真的点名该片区，可升 `support`（docs/01 §10）
  - `.gov.cn` 域名本身即政府网站，credibility 记 C 属误标，按 docs/07 至少 B
  - 待核=证据链不达标；若有 A/B 级 .gov.cn 来源且含快照，证据链已达标，升 `运行中`

只写 `data/clean/by_province/` 与 master 的 map 表，跑完接 merge -> build -> validate。
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
CLEAN = ROOT / "data" / "clean"
DB = ROOT / "data" / "db" / "片区库.sqlite3"


def read(p):
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
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    areas = {r["area_id"]: dict(r) for r in con.execute(
        "select area_id, name, name_norm, status from area where record_state='active'")}
    pol_path = {r["policy_id"]: r["local_path"] for r in con.execute("select policy_id, local_path from policy")}

    # 1) mention -> support：政策快照里点名该片区
    up = 0
    for p in sorted(BP.glob("*-area_policy_map.csv")):
        hdr, rows = read(p)
        ch = False
        for r in rows:
            if r.get("rel") != "mention":
                continue
            aid = r.get("area_id")
            a = areas.get(aid)
            if not a:
                continue
            lp = pol_path.get(r.get("policy_id") or "")
            if not lp:
                continue
            f = ROOT / lp
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            nm, nn = (a["name"] or "").strip(), (a["name_norm"] or "").strip()
            if nm and nm in text:
                r["rel"] = "support"
                r["note"] = (r.get("note") or "")[:100]
                up += 1
                ch = True
        if ch and not dry:
            write(p, hdr, rows)
    print("mention→support", up)

    # 2) credibility C -> B（.gov.cn）
    cb = 0
    for p in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(p)
        ch = False
        for r in rows:
            if (r.get("credibility") or "") == "C" and ".gov.cn" in (r.get("url") or ""):
                r["credibility"] = "B"
                cb += 1
                ch = True
        if ch and not dry:
            write(p, hdr, rows)
    print("credibility C→B（.gov.cn）", cb)

    # 3) 待核 -> 运行中：有 A/B .gov.cn 来源且有快照
    up_pending = 0
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        ch = False
        for r in rows:
            if r.get("status") != "待核":
                continue
            aid = r.get("area_id")
            n = con.execute("""select count(*) from source s join area_source_map m on m.source_id=s.source_id
                where m.area_id=? and s.url like '%gov.cn%' and s.credibility in ('A','B')
                and coalesce(s.local_path,'')<>''""", (aid,)).fetchone()[0]
            if n:
                r["status"] = "运行中"
                up_pending += 1
                ch = True
        if ch and not dry:
            write(p, hdr, rows)
    print("待核→运行中", up_pending)
    if dry:
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
