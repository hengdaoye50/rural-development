# -*- coding: utf-8 -*-
"""口径实体化：给 area 加 `admin_level`/`agency_level`，给 source 加 `excerpt_status`。

定义（写进 docs/02）：
  - `admin_level`   空间层级：片区所在县级或市级单元（county / city）——回答「它落在哪一级」
  - `agency_level`  设立/命名主体层级：province / city / county / town / unknown——回答「谁给它命名」
                    规则：primary 政策 issuer_level 优先；无政策看 issuer 关键词；直辖市特例：
                    区级主体记 city、市级主体记 province（用户在 2026-11 裁定「直辖市的区按地市级算」）
  - `excerpt_status` verbatim（逐字命中快照）/ digest（导航性摘要）/ missing（无快照）

只写 `data/clean/by_province/`，改完接 merge_by_province -> build_db -> validate_db。
幂等：已存在列则只补空值。

用法：
  python scripts/migrate_level_fields.py --dry-run
  python scripts/migrate_level_fields.py
"""
from __future__ import annotations

import csv
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
PROV_KW = re.compile(r"(省|自治区|直辖市|省委|省人民政府|自治区党委|自治区人民政府)")
CITY_KW = re.compile(r"(市|市委|市人民政府|地区行署|州人民政府|州委)")
COUNTY_KW = re.compile(r"(县|区|旗|县人民政府|区人民政府|县委|区委)")
TOWN_KW = re.compile(r"(镇|乡|街道办事处)")


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
    region = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    primary, support = {}, {}
    for r in con.execute("""select m.area_id, p.issuer_level, m.rel from area_policy_map m
                            join policy p on p.policy_id = m.policy_id
                            where m.rel in ('primary','support')"""):
        if r["rel"] == "primary":
            primary.setdefault(r["area_id"], r["issuer_level"])
        else:
            support.setdefault(r["area_id"], r["issuer_level"])

    def agency(aid: str, prov: str, county: str, issuer: str) -> str:
        lv = (primary.get(aid) or "").strip()
        if not lv:
            txt = issuer or ""
            if PROV_KW.search(txt):
                lv = "province"
            elif CITY_KW.search(txt):
                lv = "city"
            elif COUNTY_KW.search(txt):
                lv = "county"
            elif TOWN_KW.search(txt):
                lv = "town"
        if not lv:
            lv = (support.get(aid) or "").strip()
        if lv not in ("province", "city", "county", "town"):
            return "unknown"
        if prov in MUNI:
            if lv == "county" and county[:2] == prov[:2]:
                return "city"      # 直辖市的区按地市级
            if lv == "city":
                return "province"  # 直辖市市级
        return lv

    stats = dict(area_rows=0, admin_fill=0, agency_fill=0, src_rows=0, verbatim=0, digest=0, missing=0)
    for ap in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(ap)
        if "admin_level" not in hdr:
            hdr += ["admin_level", "agency_level"]
        for r in rows:
            cc = (r.get("county_code") or "").strip()
            reg = region.get(cc)
            if not (r.get("admin_level") or "").strip():
                r["admin_level"] = (reg["level"] if reg else "") or "unknown"
                stats["admin_fill"] += 1
            if not (r.get("agency_level") or "").strip():
                r["agency_level"] = agency(r.get("area_id", ""), r.get("province_code", ""), cc,
                                           r.get("issuer", ""))
                stats["agency_fill"] += 1
            stats["area_rows"] += 1
        if not dry:
            write(ap, hdr, rows)

    for sp in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(sp)
        if "excerpt_status" not in hdr:
            hdr += ["excerpt_status"]
        for s in rows:
            stats["src_rows"] += 1
            if (s.get("excerpt_status") or "").strip():
                continue
            lp = (s.get("local_path") or "").strip()
            f = ROOT / lp if lp else None
            if not lp or not f.is_file():
                s["excerpt_status"] = "missing"
                stats["missing"] += 1
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            ex = (s.get("excerpt") or "").strip()
            if ex and (ex in text or PUN.sub("", ex) in PUN.sub("", text)):
                s["excerpt_status"] = "verbatim"
                stats["verbatim"] += 1
            else:
                s["excerpt_status"] = "digest"
                stats["digest"] += 1
        if not dry:
            write(sp, hdr, rows)

    print(("dry-run：" if dry else "已完成：") + str(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
