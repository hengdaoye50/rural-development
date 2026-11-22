# -*- coding: utf-8 -*-
"""导出地图数据：省级/市级边界 GeoJSON + 分省分市分县汇总 CSV（可重复跑）。

边界来源：阿里 DataV 行政区划边界（`geo.datav.aliyun.com/areas_v3/bound/{code}_full.json`），
首次运行下载并缓存到 `data/geo/`，之后离线复用；没有缓存且无网络时只出 CSV。

字段（properties）：
  code/name/level      行政区划
  areas                在册片区数（active）
  main                主统计（A+B）
  wide                宽统计（A+B+C）
  pending             待核
  pending_share       待核占比
  strong              有 primary/support 的活跃记录
  policy              该省/市政策文件数
  counties            覆盖县数（county_code 去重）
  belt                象征单元数（仅省级）

用法：
  python scripts/export_map_data.py                 # 有缓存就用缓存
  python scripts/export_map_data.py --fetch         # 强制刷新边界
  python scripts/export_map_data.py --no-fetch      # 只用缓存，不联网
产出：
  data/export/map/provinces.geojson
  data/export/map/cities.geojson
  data/export/map/分省汇总.csv / 分市汇总.csv / 分县汇总.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
GEO = ROOT / "data" / "geo"
OUT = ROOT / "data" / "export" / "map"
BASE = "https://geo.datav.aliyun.com/areas_v3/bound/{code}_full.json"


def fetch_json(code: str, force: bool) -> dict | None:
    GEO.mkdir(parents=True, exist_ok=True)
    p = GEO / f"{code}_full.json"
    if p.exists() and not force:
        return json.loads(p.read_text(encoding="utf-8"))
    try:
        import requests
        r = requests.get(BASE.format(code=code), timeout=30,
                         headers={"User-Agent": "Mozilla/5.0 dsh-map-export"})
        r.raise_for_status()
        data = r.json()
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
    except Exception as e:  # noqa: BLE001
        print(f"  ! 边界获取失败 {code}: {e}")
        return None


def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    tmp.replace(path)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="强制刷新边界缓存")
    ap.add_argument("--no-fetch", action="store_true", help="不联网，只用缓存")
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    names = {r["region_code"]: dict(r) for r in con.execute("select * from region")}

    rows = [dict(r) for r in con.execute("""
        select a.area_id, a.province_code, a.city_code, a.county_code, a.status,
               c.caliber_group g, c.in_main_stat m, c.in_scope sc,
               (select count(*) from area_policy_map p where p.area_id=a.area_id
                 and p.rel in ('primary','support')) nh
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active'""")]
    belts = [dict(r) for r in con.execute(
        "select province_code, count(*) n from belt where record_state='active' group by 1")]
    pol = {r["province_code"]: r["n"] for r in con.execute(
        "select province_code, count(*) n from policy group by 1")}

    def agg(key: str, code: str) -> dict:
        sub = [r for r in rows if r[key] == code]
        pend = sum(1 for r in sub if r["status"] == "待核")
        return {
            "areas": len(sub), "pending": pend,
            "pending_share": round(pend / len(sub) * 100, 1) if sub else 0,
            "main": sum(1 for r in sub if r["m"]),
            "wide": sum(1 for r in sub if r["sc"] and r["g"] in ("A", "B", "C")),
            "strong": sum(1 for r in sub if r["nh"]),
            "counties": len({r["county_code"] for r in sub if r["county_code"]}),
        }

    # 省级
    prov_rows = []
    for code, reg in names.items():
        if reg["level"] != "province":
            continue
        a = agg("province_code", code)
        prov_rows.append({
            "code": code, "name": reg["name"], "level": "province",
            **a, "belt": next((b["n"] for b in belts if b["province_code"] == code), 0),
            "policy": pol.get(code, 0),
        })
    prov_rows.sort(key=lambda x: -x["areas"])

    # 市级
    city_codes = {r["city_code"] for r in rows if r["city_code"]}
    city_rows = []
    for code in sorted(city_codes):
        reg = names.get(code)
        a = agg("city_code", code)
        city_rows.append({
            "code": code, "name": reg["name"] if reg else code, "level": "city",
            "province_code": (reg or {}).get("parent_code", ""),
            **a,
        })

    # 县级
    seen = {}
    for r in rows:
        cc = r["county_code"]
        if not cc:
            continue
        s = seen.setdefault(cc, {"code": cc, "name": (names.get(cc) or {}).get("name", cc),
                                 "province_code": r["province_code"], "areas": 0,
                                 "main": 0, "pending": 0})
        s["areas"] += 1
        s["main"] += 1 if r["m"] else 0
        s["pending"] += 1 if r["status"] == "待核" else 0
    county_rows = sorted(seen.values(), key=lambda x: -x["areas"])

    write_csv(OUT / "分省汇总.csv", prov_rows,
              ["code", "name", "areas", "main", "wide", "pending", "pending_share",
               "strong", "counties", "belt", "policy"])
    write_csv(OUT / "分市汇总.csv", city_rows,
              ["code", "name", "province_code", "areas", "main", "wide", "pending",
               "pending_share", "strong", "counties"])
    write_csv(OUT / "分县汇总.csv", county_rows,
              ["code", "name", "province_code", "areas", "main", "pending"])
    print(f"CSV -> {OUT.relative_to(ROOT)}：省 {len(prov_rows)} / 市 {len(city_rows)} / 县 {len(county_rows)}")

    if args.no_fetch:
        print("--no-fetch：跳过 GeoJSON")
        return 0

    # GeoJSON
    nat = fetch_json("100000", args.fetch)
    if not nat:
        print("无省级边界，GeoJSON 跳过（CSV 已生成）")
        return 0
    feat_prov = []
    stats = {r["code"]: r for r in prov_rows}
    for f in nat.get("features", []):
        fp = f.get("properties", {})
        code = str(fp.get("adcode", ""))
        s = stats.get(code) or {}
        props = {"code": code, "name": fp.get("name", ""), "level": "province",
                 "has_areas": bool(s.get("areas"))}
        for k in ("areas", "main", "wide", "pending", "pending_share",
                  "strong", "counties", "belt", "policy"):
            props[k] = s.get(k, 0)
        feat_prov.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
    gj = {"type": "FeatureCollection",
          "features": feat_prov,
          "properties": {"generated": "export_map_data.py", "metric": "area counts"}}
    (OUT / "provinces.geojson").write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"provinces.geojson：{len(feat_prov)} 个要素")

    # 市级：逐省取边界再合并（港澳台无边界，跳过；直辖市用市域统计套到各区）
    city_stats = {r["code"]: r for r in city_rows}
    MUNI = {"110000", "120000", "310000", "500000"}
    SKIP = {"710000", "810000", "820000"}
    feats: list[dict] = []
    for p in prov_rows:
        code = p["code"]
        if code in SKIP:
            continue
        d = fetch_json(code, args.fetch)
        if not d:
            continue
        muni = code in MUNI
        for f in d.get("features", []):
            fp = f.get("properties", {})
            c = str(fp.get("adcode", ""))
            s = city_stats.get(c) or (p if muni else None)
            props = {"code": c, "name": fp.get("name", ""),
                     "level": "district" if muni else "city",
                     "province_code": code, "is_municipality": muni,
                     "has_areas": bool(s and s.get("areas"))}
            for k in ("areas", "main", "wide", "pending", "pending_share", "strong", "counties"):
                props[k] = (s or {}).get(k, 0)
            feats.append({"type": "Feature", "properties": props, "geometry": f.get("geometry")})
    gj = {"type": "FeatureCollection", "features": feats}
    (OUT / "cities.geojson").write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"cities.geojson：{len(feats)} 个要素")
    write_csv(OUT / "分市汇总.csv",
              [f["properties"] for f in feats],
              ["code", "name", "level", "province_code", "is_municipality", "areas", "main",
               "wide", "pending", "pending_share", "strong", "counties"])
    print(f"分市汇总.csv 已按边界要素重写：{len(feats)} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
