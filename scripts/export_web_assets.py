# -*- coding: utf-8 -*-
"""生成站点前端用的数据切片：web/assets/data/*.js（经典脚本，file:// 可用）。

产出：
  web/assets/data/summary.js  → window.RD = { snapshot, totals, provinces, years, types, groups }
  web/assets/data/provinces.js → window.RD_GEO = FeatureCollection（省界 + 统计）

统计口径全部来自 `area_caliber` 视图，与 `area_caliber`/`macro_unit` 一致，不在这里重算口径。
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
GEO = ROOT / "data" / "export" / "map" / "provinces.geojson"
OUT = ROOT / "web" / "assets" / "data"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    q = lambda s, p=(): con.execute(s, p).fetchone()[0]  # noqa: E731

    regions = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    rows = [dict(r) for r in con.execute("""
        select a.area_id, a.province_code, a.city_code, a.county_code, a.status, a.type_code,
               c.caliber_group g, c.in_main_stat m, c.in_scope sc
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active'""")]
    belts = {r["province_code"]: r["n"] for r in con.execute(
        "select province_code, count(*) n from belt where record_state='active' group by 1")}
    policy = {r["province_code"]: r["n"] for r in con.execute(
        "select province_code, count(*) n from policy group by 1")}

    def stat(sub: list[dict]) -> dict:
        pend = sum(1 for r in sub if r["status"] == "待核")
        return {
            "areas": len(sub),
            "main": sum(1 for r in sub if r["m"]),
            "wide": sum(1 for r in sub if r["sc"] and r["g"] in ("A", "B", "C")),
            "pending": pend,
            "pending_share": round(pend / len(sub) * 100, 1) if sub else 0,
            "counties": len({r["county_code"] for r in sub if r["county_code"]}),
        }

    provinces = []
    for code, reg in regions.items():
        if reg["level"] != "province":
            continue
        s = stat([r for r in rows if r["province_code"] == code])
        provinces.append({
            "code": code, "name": reg["name"], **s,
            "belt": belts.get(code, 0),
            "policy": policy.get(code, 0),
        })
    provinces.sort(key=lambda p: -p["areas"])

    totals = {
        "areas": len(rows),
        "main": sum(1 for r in rows if r["m"]),
        "wide": sum(1 for r in rows if r["sc"] and r["g"] in ("A", "B", "C")),
        "pending": sum(1 for r in rows if r["status"] == "待核"),
        "macro": q("select count(*) from macro_unit"),
        "belt": q("select count(*) from belt where record_state='active'"),
        "policy": q("select count(*) from policy"),
        "source": q("select count(*) from source"),
        "county_n": q("select count(*) from region where level='county'"),
        "county_all": len({r["county_code"] for r in rows if r["county_code"]}),
        "county_map": q("""select count(distinct m.region_code) from area_region_map m
                            join area a on a.area_id=m.area_id where a.record_state='active'"""),
        "policy_chars": q("select coalesce(sum(full_text_chars),0) from policy"),
    }
    year_rows = [dict(r) for r in con.execute("""
        select a.area_id, substr(a.founded_ymd,1,4) y, a.status, c.caliber_group g, c.in_scope sc, c.in_main_stat m
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active' and a.founded_ymd is not null and a.founded_ymd<>''""")]
    by_year: dict[str, dict] = {}
    for r in year_rows:
        y = r["y"]
        if not y:
            continue
        d = by_year.setdefault(y, {"all": 0, "main": 0})
        d["all"] += 1
        d["main"] += 1 if r["m"] else 0
    types = Counter(r["type_code"] for r in rows)
    groups = Counter(r["g"] for r in rows if r["status"] != "待核")

    # 证据强度（与 areas.js 的 ev 同源：strong ⟺ 有 primary/support）
    ev_rows = [dict(x) for x in con.execute("""
        select a.area_id,
               (select count(*) from area_policy_map m where m.area_id=a.area_id
                 and m.rel in ('primary','support')) hard,
               (select count(*) from area_policy_map m where m.area_id=a.area_id
                 and m.rel='mention') men
        from area a where a.record_state='active'""")]
    evidence = {
        "strong": sum(1 for r in ev_rows if r["hard"]),
        "weak": sum(1 for r in ev_rows if not r["hard"] and r["men"]),
        "none": sum(1 for r in ev_rows if not r["hard"] and not r["men"]),
        "multi": sum(1 for r in ev_rows if r["hard"] >= 2),
    }
    n_village = q("select count(*) from area where record_state='active' "
                  "and scale_villages is not null and scale_villages <> ''")
    n_year = len({r["area_id"] for r in year_rows})
    areas_n = totals["areas"] or 1
    quality = {
        "cite_rate": round(totals["main"] / areas_n * 100, 1),
        "named_rate": round(evidence["strong"] / areas_n * 100, 1),
        "pending_rate": round(totals["pending"] / areas_n * 100, 1),
        "year_rate": round(n_year / areas_n * 100, 1),
        "village_rate": round(n_village / areas_n * 100, 1),
        "multi_rate": round(evidence["multi"] / areas_n * 100, 1),
        "year_missing": totals["areas"] - n_year,
        "village_missing": totals["areas"] - n_village,
    }

    geojson = None
    if GEO.exists():
        geojson = json.loads(GEO.read_text(encoding="utf-8"))
        pstat = {p["code"]: p for p in provinces}
        for f in geojson["features"]:
            fp = f.get("properties", {})
            code = str(fp.get("code") or fp.get("adcode") or "")
            fp["code"] = code
            s = pstat.get(code)
            fp["has_areas"] = bool(s and s["areas"])
            if s:
                for k in ("areas", "main", "wide", "pending", "pending_share",
                          "counties", "belt", "policy"):
                    fp[k] = s.get(k, 0)

    data = {
        "snapshot": date.today().isoformat(),
        "built": date.today().isoformat(),
        "totals": totals,
        "provinces": provinces,
        "years": dict(sorted(by_year.items())),
        "types": dict(types),
        "groups": dict(groups),
        "evidence": evidence,
        "quality": quality,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.js").write_text(
        "window.RD = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")

    # 逐条片区（检索页用）：一行一区，字段与 JSON 键一致
    rel = {}
    for r in con.execute("select area_id, rel from area_policy_map"):
        rel.setdefault(r["area_id"], set()).add(r["rel"])
    areas = []
    for r in con.execute("""
        select a.area_id, a.name, a.province_code, a.city_code, a.county_code, a.type_code,
               a.setup_kind, a.status, a.founded_ymd, a.scale_villages,
               c.caliber_group g, c.in_main_stat m
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active' order by a.area_id"""):
        r = dict(r)
        s = rel.get(r["area_id"], set())
        areas.append({
            "id": r["area_id"], "name": r["name"],
            "prov": r["province_code"], "city": r["city_code"], "county": r["county_code"],
            "prov_name": (regions.get(r["province_code"]) or {}).get("name", ""),
            "city_name": (regions.get(r["city_code"]) or {}).get("name", ""),
            "county_name": (regions.get(r["county_code"]) or {}).get("name", ""),
            "type": r["type_code"], "setup": r["setup_kind"] or "unknown",
            "status": r["status"], "ymd": r["founded_ymd"] or "",
            "g": r["g"] or "", "m": 1 if r["m"] else 0,
            "villages": r["scale_villages"] or "",
            "ev": "强" if ({"primary", "support"} & s) else ("弱" if "mention" in s else "无"),
            "npol": len([x for x in s if x in ("primary", "support")]),
        })
    (OUT / "areas.js").write_text(
        "window.RD_AREAS = " + json.dumps(areas, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"areas.js：{len(areas)} 条")
    if geojson:
        (OUT / "provinces.js").write_text(
            "window.RD_GEO = " + json.dumps(geojson, ensure_ascii=False) + ";\n", encoding="utf-8")

    print(f"summary.js：省 {len(provinces)}｜active {totals['areas']}｜M {totals['macro']}｜主统计 {totals['main']}")
    if geojson:
        print(f"provinces.js：{len(geojson['features'])} 要素")
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
