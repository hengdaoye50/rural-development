# -*- coding: utf-8 -*-
"""生成「名称不含『片区』且无政策依据」的逐条裁定表（只读 + 落 CSV）。

为什么单列：这类记录的名字来自官方名单（如天津 12 个乡村旅游示范片区，
名单里就叫「悠闲山谷，幻彩田园」），但库里没有 primary/support。
不能按名称批量下架，也不能一律升格——需要逐条看来源与名单状态。

建议列取值：
  保留   省级名单已对账（roster matched），名称即官方名，只是缺政策挂接
  待核   有 A/B 来源但缺名单对账，先维持待核
  拆分   名称是区域级（先行区/示范区/示范点/试验区），应拆到县或改台账 not_area
  存疑   仅有 C 级媒体来源，名称未证实

用法：python scripts/build_brand_name_decisions.py
产出：data/stage/candidates/brand-name-decisions-{date}.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
OUT = ROOT / "data" / "stage" / "candidates" / f"brand-name-decisions-{date.today()}.csv"
REGION_WORDS = re.compile(r"先行区|示范区|示范点|试验区|示范带|示范圈|走廊|廊道")
STRONG_TIERS = {"core", "exact", "stripped", "tail"}


def load_tiers() -> dict[str, set[str]]:
    """从 link-veracity.csv 取每个片区的点名级证据（有则说明政策正文真点名）。"""
    p = ROOT / "reports" / "qa" / "link-veracity.csv"
    out: dict[str, set[str]] = {}
    if not p.exists():
        return out
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["area_id"], set()).add(r["tier"])
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    roster = {r["province_code"]: r["status"] for r in con.execute(
        "select province_code, status from province_roster")}
    tiers = load_tiers()
    rows = []
    for a in con.execute("""
        select a.area_id, a.name, a.province_code, a.city_code, a.county_code, a.status,
               a.summary, a.cover_desc,
               (select count(*) from area_policy_map p where p.area_id=a.area_id
                 and p.rel in ('primary','support')) npol,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel='mention') nmen
        from area a where a.record_state='active'"""):
        name = a["name"] or ""
        if "片区" in name or a["npol"]:
            continue
        src = con.execute("""
            select s.credibility, s.publisher, s.url, s.title
            from area_source_map m join source s on s.source_id=m.source_id
            where m.area_id=? order by case s.credibility when 'A' then 1 when 'B' then 2
            when 'C' then 3 else 4 end limit 1""", (a["area_id"],)).fetchone()
        cred = (src["credibility"] if src else "") or ""
        rst = roster.get(a["province_code"], "")
        tset = tiers.get(a["area_id"], set())
        strong = bool(tset & STRONG_TIERS)
        if strong:
            rec, why = "保留", "政策正文点名级证据（tier 强），只是 rel 未升 primary"
        elif REGION_WORDS.search(name):
            rec, why = "拆分", "名称是区域级（先行区/示范区/示范点），不是单一县以下片区"
        elif rst == "matched" and tset:
            rec, why = "待核", f"名单已对账但正文只提地名（tier={'/'.join(sorted(tset))}），证据不足"
        elif cred in ("A", "B"):
            rec, why = "待核", f"有 {cred} 级来源但名单未对账、正文未点名，先维持待核"
        else:
            rec, why = "存疑", f"仅 {cred or '无'} 级来源，名称未证实"
        rows.append({
            "area_id": a["area_id"], "name": name, "province_code": a["province_code"],
            "city_code": a["city_code"], "county_code": a["county_code"], "status": a["status"],
            "credibility": cred, "publisher": (src["publisher"] if src else "") or "",
            "url": (src["url"] if src else "") or "",
            "roster_status": rst, "建议": rec, "理由": why,
            "cover_desc": (a["cover_desc"] or "")[:120],
        })
    con.close()
    cnt = Counter(r["建议"] for r in rows)
    print(f"名称不含「片区」且无政策依据：{len(rows)} 条｜{dict(cnt)}")
    for r in rows:
        print(f"  [{r['建议']}] {r['area_id']} {r['name'][:26]}｜{r['credibility'] or '-'}｜{r['roster_status'] or '-'}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["area_id", "name", "province_code", "city_code", "county_code", "status",
            "credibility", "publisher", "roster_status", "建议", "理由", "url", "cover_desc"]
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    tmp.replace(OUT)
    print(f"\n裁定表 -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
