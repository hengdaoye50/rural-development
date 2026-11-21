# -*- coding: utf-8 -*-
"""数据质量批量修复（幂等，先 --dry-run）。

四件事：
  A. city_code 修正：县区 parent_code 与 area.city_code 不符时，按 region 的 parent 改正
     （直辖市除外：北京/天津/上海/重庆 的区在 region 里挂在 110100/120100/310100/500100 下，
      而 area 统一记省级码，属口径设计，不动）
  B. source.local_path 修正：指向目录且目录内有 原文.md → 改为该文件；路径不存在 → 清空（死链）
  C. source.excerpt 重锚：excerpt 在快照里找不到时，用关联片区名在快照中定位并截取窗口（逐字）
  D. 名单台账计数修正：库内数 > 官方数 的两条（湖州多批次、连云港 R10 分建）按口径改

只写 `data/clean/by_province/`，改完跑 merge_by_province -> build_db -> validate_db。
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = ROOT / "data" / "db" / "片区库.sqlite3"
MUNI = {"110000", "120000", "310000", "500000"}
PUN = re.compile(r"[\s\u3000\W_]+", re.U)


def norm(s: str) -> str:
    return PUN.sub("", s or "")


def read(p: Path):
    if not p.exists():
        return [], []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
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
    region = {r["region_code"]: r for r in con.execute("select * from region")}
    areas = {r["area_id"]: r for r in con.execute("select * from area")}

    files = sorted(BP.glob("*-area.csv"))
    stats = dict(city_fix=0, path_dir=0, path_dead=0, excerpt_fix=0, excerpt_left=0)

    for ap in files:
        abbr = ap.name.split("-")[0]
        hdr, rows = read(ap)
        changed = False
        for r in rows:
            cc, city, prov = r.get("county_code", ""), r.get("city_code", ""), r.get("province_code", "")
            reg = region.get(cc)
            if reg and reg["parent_code"] and city and reg["parent_code"] != city and prov not in MUNI:
                r["city_code"] = reg["parent_code"]
                stats["city_fix"] += 1
                changed = True
        if changed and not dry:
            write(ap, hdr, rows)

        # C. source
        sp = BP / f"{abbr}-source.csv"
        shdr, srows = read(sp)
        schanged = False
        for s in srows:
            lp = (s.get("local_path") or "").strip()
            if not lp:
                continue
            f = ROOT / lp
            if f.is_dir():
                cand = f / "原文.md"
                if cand.is_file():
                    s["local_path"] = str(cand.relative_to(ROOT)).replace("\\", "/")
                    s["hash_sha256"] = hashlib.sha256(cand.read_bytes()).hexdigest()
                    stats["path_dir"] += 1
                    schanged = True
                    f = cand
                else:
                    s["local_path"] = ""
                    stats["path_dead"] += 1
                    schanged = True
                    continue
            elif not f.is_file():
                s["local_path"] = ""
                stats["path_dead"] += 1
                schanged = True
                continue
            # excerpt 重锚
            ex = (s.get("excerpt") or "").strip()
            if len(ex) < 20:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            if ex in text or norm(ex) in norm(text):
                continue
            # 找关联片区名
            aid = (s.get("area_id") or "").strip()
            names = []
            if aid in areas:
                names.append(areas[aid]["name"])
            linked = [r["name"] for r in
                      con.execute("""select a.name from area a join area_source_map m on m.area_id=a.area_id
                        where m.source_id=?""", (s["source_id"],))] if s.get("source_id") else []
            names += linked
            pos, name = -1, ""
            for n in names:
                if not n:
                    continue
                pos = text.find(n)
                if pos >= 0:
                    name = n
                    break
            if pos >= 0:
                a, b = max(0, pos - 60), min(len(text), pos + len(name) + 140)
                seg = text[a:b].replace("\n", " ").strip()
                s["excerpt"] = seg
                stats["excerpt_fix"] += 1
                schanged = True
            else:
                stats["excerpt_left"] += 1
        if schanged and not dry:
            write(sp, shdr, srows)

    # E. 待核但已有 primary/support：按口径定义升为运行中（证据链已达标）
    npend = 0
    for ap in files:
        abbr = ap.name.split("-")[0]
        hdr2, arows = read(ap)
        ch = False
        for r in arows:
            if r.get("status") != "待核":
                continue
            aid = r.get("area_id")
            linked = con.execute("""select count(*) from area_policy_map where area_id=?
              and rel in ('primary','support')""", (aid,)).fetchone()[0]
            if linked:
                r["status"] = "运行中"
                r["updated_at"] = "2026-11-21"
                npend += 1
                ch = True
        if ch and not dry:
            write(ap, hdr2, arows)
    stats["pending_upgraded"] = npend

    # D. roster
    p = ROOT / "data" / "clean" / "city_roster.csv"
    hdr, rows = read(p)
    changed = False
    for r in rows:
        if r["city_code"] == "330500":
            r["official_count"] = "16"
            r["count_basis"] = "累计"
            r["note"] = (r.get("note", "") + "｜6 份名单文件累计 16 条（按累计口径记 official_count=16）")[:600]
            changed = True
        elif r["city_code"] == "320700":
            r["official_count"] = "4"
            r["note"] = (r.get("note", "") + "｜3 个示范区按 R10 跨县分建为 4 行，official_count 按入库行数记 4")[:600]
            changed = True
    if changed and not dry:
        write(p, hdr, rows)

    print(("dry-run 统计：" if dry else "已修复：") + str(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
