# -*- coding: utf-8 -*-
"""导出前端所需数据 -> web/data.js（window.DATA），供 file:// 直接打开。

为什么不用 fetch：`file://` 下 fetch 受 CORS 限制；用 <script src="data.js"> 可直接加载。
体积控制：area 全量 1400+ 行、每行 ~18 字段，约 400–600KB，可接受。

用法：python scripts/export_web_data.py
"""
from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
WEB = ROOT / "web"
MUNI = {"110000", "120000", "310000", "500000"}
LEVEL_LABEL = {"province": "省级", "city": "地市级", "county": "县区级", "town": "乡镇级"}


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = lambda s, p=(): con.execute(s, p).fetchone()[0]  # noqa: E731

    region = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    # 每个片区的依据强度：按 area_policy_map 的 rel 归三档（与 area_caliber 口径一致）
    rels: dict[str, set[str]] = defaultdict(set)
    for r in con.execute("select area_id, rel from area_policy_map"):
        rels[r["area_id"]].add(r["rel"])

    def ev_of(aid: str) -> str:
        s = rels.get(aid, set())
        if "primary" in s or "support" in s:
            return "强"
        return "弱" if "mention" in s else "无"

    rows = []
    for a in con.execute("""select area_id, name, type_code, setup_kind, province_code, city_code,
        county_code, founded_ymd, founded_precision, status, scale_villages, issuer
        from area where record_state='active'"""):
        cc = a["county_code"]
        reg = region.get(cc)
        city_reg = region.get(a["city_code"])
        prov_reg = region.get(a["province_code"])
        cal = con.execute("select caliber_group, in_main_stat from area_caliber where area_id=?",
                          (a["area_id"],)).fetchone()
        # 层级：读实体化字段（docs/02 §1.1），不再现推
        lv = con.execute("select agency_level from area where area_id=?", (a["area_id"],)).fetchone()
        level = (lv[0] if lv else "") or ""
        rows.append({
            "id": a["area_id"], "name": a["name"], "type": a["type_code"],
            "setup": a["setup_kind"] or "unknown",
            "prov": prov_reg["name"] if prov_reg else "?", "prov_code": a["province_code"],
            "city": city_reg["name"] if city_reg else "?", "city_code": a["city_code"],
            "county": reg["name"] if reg else (cc or "?"), "county_code": cc,
            "level": LEVEL_LABEL.get(level, "不可判定"),
            "ymd": a["founded_ymd"] or "", "prec": a["founded_precision"] or "",
            "status": a["status"], "group": cal["caliber_group"] if cal else "?",
            "main": 1 if cal and cal["in_main_stat"] else 0,
            "evidence": ev_of(a["area_id"]),
            "n_pol": len([x for x in rels.get(a["area_id"], set()) if x in ("primary", "support")]),
            "villages": a["scale_villages"] or "",
        })

    # 汇总
    active = len(rows)
    pending = sum(1 for r in rows if r["status"] == "待核")
    full = active - pending
    main_n = sum(r["main"] for r in rows)
    # A–E 只在「口径内」（非待核）上统计；待核是 in_scope=0，单独计数
    groups = Counter(r["group"] for r in rows if r["status"] != "待核")
    levels = Counter(r["level"] for r in rows)
    years = Counter((r["ymd"][:4] or "未填") for r in rows)
    years_full = Counter((r["ymd"][:4] or "未填") for r in rows if r["status"] != "待核")
    hard_n = sum(1 for r in rows if r["evidence"] == "强" and r["status"] != "待核")
    provs = []
    for p in con.execute("select region_code, name from region where level='province' order by region_code"):
        code = p["region_code"]
        n = sum(1 for r in rows if r["prov_code"] == code)
        nm = sum(r["main"] for r in rows if r["prov_code"] == code)
        nf = sum(1 for r in rows if r["prov_code"] == code and r["status"] != "待核")
        provs.append({"code": code, "name": p["name"], "area": n, "main": nm, "full": nf,
                      "counties": len({r["county_code"] for r in rows if r["prov_code"] == code})})
    provs.sort(key=lambda x: -x["area"])

    # 台账
    city_rows = [dict(r) for r in con.execute(
        "select city_code, city_name, province_code, roster_name, roster_scope, official_count, "
        "in_db_count, count_basis, status, note from city_roster order by city_code")]
    prov_rows = [dict(r) for r in con.execute(
        "select province_code, roster_name, roster_scope, official_count, in_db_count, "
        "count_basis, status, note from province_roster order by province_code")]
    cname = {r["region_code"]: r["name"] for r in con.execute("select * from region where level='province'")}
    for r in city_rows:
        r["province_name"] = cname.get(r["province_code"], "")

    # 县级台账与欠账
    county_rows = [dict(r) for r in con.execute(
        "select county_code, county_name, province_code, roster_name, official_count, "
        "in_db_count, status, note from county_roster order by province_code, county_code")]
    debt = [dict(r) for r in con.execute(
        "select debt_type, count(*) as n from evidence_debt group by 1 order by 2 desc")]

    # 象征性单元 belt（示范带/圈/廊/片）：M 层总量含它们，前端必须能分别看
    belts = []
    for b in con.execute("""select belt_id, name, belt_type, theme, province_code, city_code,
        county_code, cover_desc, scale_villages, announced_ymd, issuer, record_state
        from belt where record_state='active'"""):
        cc = b["county_code"] or ""
        bel_region = region.get(cc)
        belts.append({
            "id": b["belt_id"], "name": b["name"], "type": b["belt_type"], "theme": b["theme"] or "",
            "prov": (region.get(b["province_code"]) or {}).get("name", "?"),
            "prov_code": b["province_code"],
            "city": (region.get(b["city_code"]) or {}).get("name", "?"),
            "county": bel_region["name"] if bel_region else "", "county_code": cc,
            "ymd": b["announced_ymd"] or "", "villages": b["scale_villages"] or "",
            "issuer": b["issuer"] or "", "cover": (b["cover_desc"] or "")[:120],
        })

    # 质量
    qual = {}
    ap = sorted((ROOT / "reports" / "qa").glob("data-quality-*.csv"))
    if ap:
        with ap[-1].open(encoding="utf-8-sig", newline="") as f:
            items = list(csv.DictReader(f))
        qual = {"file": ap[-1].name,
                "error": sum(1 for x in items if x["level"] == "ERROR"),
                "warn": sum(1 for x in items if x["level"] == "WARN"),
                "info": sum(1 for x in items if x["level"] == "INFO"),
                "top": [{"check": k, "n": v} for k, v in
                        Counter((x["level"], x["check"]) for x in items).most_common(8)]}
    county_n = q("select count(*) from region where level='county'")
    county_all = len({r["county_code"] for r in rows})
    county_trusted = len({r["county_code"] for r in rows if r["status"] != "待核"})
    county_map = q("""select count(distinct m.region_code) from area_region_map m
                      join area a on a.area_id=m.area_id where a.record_state='active'""")
    hard = hard_n

    DATA = {
        "meta": {"snapshot": date.today().isoformat(), "built": date.today().isoformat(),
                 "source": "data/db/片区库.sqlite3"},
        "summary": {
            "active": active, "pending": pending, "full": full, "main": main_n,
            "wide": groups["A"] + groups["B"] + groups["C"],
            "groups": {k: groups[k] for k in "ABCDE"},
            "macro": q("select count(*) from macro_unit"),
            "belt": q("select count(*) from belt"),
            "policy": q("select count(*) from policy"), "source_n": q("select count(*) from source"),
            "county_n": county_n, "county_all": county_all, "county_trusted": county_trusted,
            "county_map": county_map,
            "hard": hard, "hard_pct": round(hard / full * 100, 1) if full else 0,
            "levels": {k: levels[k] for k in ("省级", "地市级", "县区级", "乡镇级", "不可判定")},
            "years": dict(sorted(years.items())), "years_full": dict(sorted(years_full.items())),
            "province_roster": {k: sum(1 for r in prov_rows if r["status"] == k) for k in
                                ("matched", "partial", "count_only", "not_area", "none")},
            "city_roster": {k: sum(1 for r in city_rows if r["status"] == k) for k in
                            ("matched", "partial", "count_only", "not_area", "none")},
        },
        "provinces": provs,
        "areas": rows,
        "belts": belts,
        "policies_by_kind": {r["k"]: r["n"] for r in (
            {"k": x[0], "n": x[1]} for x in con.execute(
                "select coalesce(nullif(source_kind,''),'(空)'), count(*) from policy group by 1"))},
        "city_roster": city_rows,
        "province_roster": prov_rows,
        "county_roster": county_rows,
        "debt": debt,
        "quality": qual,
    }
    WEB.mkdir(parents=True, exist_ok=True)
    js = "window.DATA = " + json.dumps(DATA, ensure_ascii=False) + ";\n"
    (WEB / "data.js").write_text(js, encoding="utf-8")
    print("OK -> web/data.js", f"{len(js)/1024:.0f}KB", f"areas={len(rows)} belts={len(belts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
