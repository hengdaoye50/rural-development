# -*- coding: utf-8 -*-
"""2022+ 体检（第二版）：年份出处改为「来源快照 + 政策标题/文号」多路核对。"""
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(".")
c = sqlite3.connect("data/db/片区库.sqlite3")
c.row_factory = sqlite3.Row
prov = {r["region_code"]: r["name"] for r in c.execute("select region_code,name from region")}

rows = [dict(r) for r in c.execute("""
  select a.area_id, a.name, a.name_norm, a.province_code, a.county_code, a.founded_ymd,
         a.founded_precision, a.status,
         (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel in ('primary','support')) npol
  from area a where a.record_state='active' and a.founded_ymd >= '2022'""")]

def sources(aid):
    out = []
    for s in c.execute("""select s.url, s.title, s.published_ymd, s.local_path from area_source_map m
                          join source s on s.source_id=m.source_id where m.area_id=?""", (aid,)):
        out.append(("src", s["title"] or "", s["published_ymd"] or "", s["local_path"] or ""))
    for p in c.execute("""select p.title, p.doc_no, p.issued_ymd, p.published_ymd from area_policy_map m
                          join policy p on p.policy_id=m.policy_id where m.area_id=?""", (aid,)):
        out.append(("pol", (p["title"] or "") + " " + (p["doc_no"] or ""),
                    (p["issued_ymd"] or p["published_ymd"] or ""), ""))
    return out

stats = Counter()
missing = []
for r in rows:
    year = r["founded_ymd"][:4]
    found = False
    has_snap = False
    for kind, title, ymd, snap in sources(r["area_id"]):
        if ymd.startswith(year) or year in title:
            found = True
        if snap:
            p = ROOT / snap
            if p.exists():
                has_snap = True
                t = p.read_text(encoding="utf-8")
                i = t.find(year)
                while i >= 0:
                    seg = t[max(0, i - 40): i + 50]
                    if not any(k in seg for k in ("ICP", "备案", "许可证")):
                        found = True
                        break
                    i = t.find(year, i + 1)
    if found:
        stats["有出处"] += 1
    else:
        key = "无快照且元数据不含该年" if not has_snap else "快照与元数据均无该年"
        stats[key] += 1
        missing.append((r, key))

print("2022+ 共", len(rows), "条")
for k, v in stats.items():
    print(f"  {k}: {v}")
byprov = Counter(prov.get(r["province_code"], "?") for r, _ in missing)
print("\n缺年份出处按省：", dict(byprov.most_common()))
print("\n前 25 条：")
for r, k in missing[:25]:
    print(f"  {r['area_id']} {r['name']}｜{prov.get(r['county_code'],'')}｜{r['founded_ymd']}｜{r['status']}｜{k}")

# 同名重复
names = defaultdict(list)
for r in rows:
    names[r["name_norm"]].append(r)
dups = {k: v for k, v in names.items() if len(v) > 1}
print(f"\n同名重复 {len(dups)} 组")
for k, v in dups.items():
    print("  " + k + " -> " + "；".join(f"{x['area_id']}@{prov.get(x['county_code'],'')}" for x in v))
