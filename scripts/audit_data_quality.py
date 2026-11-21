# -*- coding: utf-8 -*-
"""数据质量审计：结构一致性 / 证据链 / 口径自洽 / 区划归属，输出分级清单。

只读，不改数据。每条问题带严重级别：
  ERROR   数据本身错（重复、悬空、非法码、哈希不符）——必须修
  WARN    口径或证据可疑（弱证据、待核却挂了 primary、名单台账数字不符）
  INFO    提示性（如直筒子市用市码当县码）

用法：
  python scripts/audit_data_quality.py
  python scripts/audit_data_quality.py --csv reports/qa/data-quality-2026-11-21.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows: list[dict] = []

    def rec(level: str, check: str, ident: str, detail: str) -> None:
        rows.append(dict(level=level, check=check, id=ident, detail=detail))

    # ---------- 基础集合 ----------
    areas = {r["area_id"]: r for r in con.execute("select * from area")}
    active = {k: v for k, v in areas.items() if v["record_state"] == "active"}
    belts = {r["belt_id"]: r for r in con.execute("select * from belt")}
    sources = {r["source_id"]: r for r in con.execute("select * from source")}
    policies = {r["policy_id"]: r for r in con.execute("select * from policy")}
    region = {r["region_code"]: r for r in con.execute("select * from region")}
    county_region = {k: v for k, v in region.items() if v["level"] == "county"}

    # ---------- 1. 主键/重复 ----------
    dup = [k for k, v in Counter(r["area_id"] for r in con.execute("select area_id from area")).items() if v > 1]
    for k in dup:
        rec("ERROR", "area_id 重复", k, "主表主键重复")
    seen: dict[tuple, list[str]] = defaultdict(list)
    for a in active.values():
        seen[(a["county_code"], a["name_norm"])].append(a["area_id"])
    for key, ids in seen.items():
        if len(ids) > 1:
            rec("ERROR", "同县同名重复", ",".join(ids), f"{key[0]} {key[1]}")

    # ---------- 2. 区划归属 ----------
    for a in active.values():
        aid, cc, city, prov = a["area_id"], a["county_code"], a["city_code"], a["province_code"]
        if not cc:
            rec("ERROR", "缺 county_code", aid, a["name"])
            continue
        reg = region.get(cc)
        if not reg:
            rec("ERROR", "county_code 不在 region", aid, f"{cc} {a['name']}")
        else:
            if reg["name"] == reg["region_code"]:
                rec("ERROR", "县码是占位行", aid, f"{cc} {a['name']}")
            if reg["level"] != "county":
                rec("INFO", "county_code 非县级（直筒子市/功能区）", aid, f"{cc} {reg['level']} {a['name']}")
            elif reg["parent_code"] and city and reg["parent_code"] != city:
                if prov in {"110000", "120000", "310000", "500000"} and city == prov:
                    pass  # 直辖市口径：区在 region 挂 xx0100，area 统一记省级码
                else:
                    rec("ERROR", "city_code 与县所属市不符", aid, f"{city} vs {reg['parent_code']} {a['name']}")
        if prov and cc[:2] + "0000" != prov:
            rec("ERROR", "province_code 与县码前缀不符", aid, f"{prov} vs {cc}")
        if city and city not in region:
            rec("ERROR", "city_code 不在 region", aid, f"{city} {a['name']}")
        if not con.execute("select 1 from area_region_map where area_id=?", (aid,)).fetchone():
            rec("ERROR", "缺 area_region_map 行", aid, a["name"])

    # ---------- 3. 悬空引用 ----------
    for m in con.execute("select area_id from area_region_map"):
        if m["area_id"] not in areas:
            rec("ERROR", "map 指向不存在的 area", m["area_id"], "")
    for m in con.execute("select area_id from area_policy_map union select area_id from area_source_map"):
        if m["area_id"] not in areas and m["area_id"] not in belts:
            rec("ERROR", "关联表指向不存在的实体", m["area_id"], "")
    for a in areas.values():
        fs = a["first_source_id"]
        if fs and fs not in sources:
            rec("ERROR", "first_source_id 悬空", a["area_id"], fs)
    for s in sources.values():
        if s["area_id"] and s["area_id"] not in areas and s["area_id"] not in belts:
            rec("ERROR", "source.area_id 悬空", s["source_id"], s["area_id"])

    # ---------- 4. 证据链 ----------
    for p in policies.values():
        lp = p["local_path"]
        if not lp:
            continue
        f = ROOT / lp
        if not f.is_file():
            rec("ERROR", "policy 快照缺失", p["policy_id"], lp)
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if p["hash_sha256"] and h != p["hash_sha256"]:
            rec("ERROR", "policy 哈希不符", p["policy_id"], lp)
        n = p["full_text_chars"] or 0
        actual = sum(1 for ch in f.read_text(encoding="utf-8", errors="ignore") if "\u4e00" <= ch <= "\u9fff")
        if n and abs(actual - n) / max(n, 1) > 0.2:
            rec("WARN", "policy 汉字数偏差>20%", p["policy_id"], f"记{n} 实{actual}")
    for s in sources.values():
        lp = s["local_path"]
        if not lp:
            if s["credibility"] in ("A", "B"):
                rec("WARN", "A/B 级来源缺快照", s["source_id"], s["title"][:30] if s["title"] else "")
            continue
        f = ROOT / lp
        if not f.is_file():
            rec("ERROR", "source 快照缺失", s["source_id"], lp)
            continue
        if s["hash_sha256"]:
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            if h != s["hash_sha256"]:
                rec("ERROR", "source 哈希不符", s["source_id"], lp)
        ex = (s["excerpt"] or "").strip()
        if len(ex) >= 20:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:  # noqa: BLE001
                text = ""
            if text and ex not in text:
                PUN = re.compile(r"[\s\u3000\W_]+", re.U)
                if PUN.sub("", ex) not in PUN.sub("", text):
                    rec("WARN", "excerpt 不在快照中", s["source_id"], ex[:30])

    # ---------- 5. 口径自洽 ----------
    full = len(active) - sum(1 for a in active.values() if a["status"] == "待核")
    cal_sum = con.execute("select count(*) from area_caliber where in_scope=1").fetchone()[0]
    if cal_sum != full:
        rec("ERROR", "caliber 五组之和 ≠ 在册非待核", "area_caliber", f"{cal_sum} vs {full}")
    main = con.execute("select count(*) from area_caliber where in_main_stat=1").fetchone()[0]
    ab = con.execute("select count(*) from area_caliber where in_scope=1 and caliber_group in ('A','B')").fetchone()[0]
    if main != ab:
        rec("ERROR", "主统计 ≠ A+B", "area_caliber", f"{main} vs {ab}")
    for a in active.values():
        if a["status"] == "待核":
            linked = con.execute("""select count(*) from area_policy_map where area_id=?
              and rel in ('primary','support')""", (a["area_id"],)).fetchone()[0]
            if linked:
                rec("WARN", "待核却挂了 primary/support", a["area_id"], a["name"])
    bad_date = [a["area_id"] for a in active.values()
                if a["founded_ymd"] and not DATE_RE.match(a["founded_ymd"])]
    for aid in bad_date:
        rec("ERROR", "founded_ymd 格式非法", aid, active[aid]["founded_ymd"])
    future = [a["area_id"] for a in active.values()
              if a["founded_ymd"] and a["founded_ymd"][:4] > "2026"]
    for aid in future:
        rec("WARN", "founded 年份在未来", aid, active[aid]["founded_ymd"])

    # ---------- 6. 名单台账自洽 ----------
    for r in con.execute("select * from province_roster"):
        if r["policy_id"] and r["policy_id"] not in policies:
            rec("ERROR", "roster.policy_id 悬空", r["province_code"], r["policy_id"])
        if r["in_db_count"] is not None and r["official_count"] and r["in_db_count"] > r["official_count"]:
            rec("WARN", "roster 库内数 > 官方数", r["province_code"], f"{r['in_db_count']}>{r['official_count']}")
    for r in con.execute("select * from city_roster"):
        if r["policy_id"] and r["policy_id"] not in policies:
            rec("ERROR", "city_roster.policy_id 悬空", r["city_code"], r["policy_id"])
        if r["in_db_count"] is not None and r["official_count"] and r["in_db_count"] > r["official_count"]:
            rec("WARN", "city_roster 库内数 > 官方数", r["city_code"], f"{r['in_db_count']}>{r['official_count']}")

    # ---------- 输出 ----------
    lvl_order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    rows.sort(key=lambda r: (lvl_order[r["level"]], r["check"]))
    cnt = Counter(r["level"] for r in rows)
    print(f"审计完成：ERROR {cnt['ERROR']} / WARN {cnt['WARN']} / INFO {cnt['INFO']}")
    by_check = Counter((r["level"], r["check"]) for r in rows)
    for (lv, ck), n in by_check.most_common(25):
        print(f"  [{lv}] {ck}: {n}")
    if args.csv:
        p = Path(args.csv)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["level", "check", "id", "detail"], lineterminator="\r\n")
            w.writeheader()
            w.writerows(rows)
        print("CSV ->", p)
    return 1 if cnt["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
