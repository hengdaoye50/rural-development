# -*- coding: utf-8 -*-
"""2021 年成立片区清单（含年份出处核对）。"""
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
c = sqlite3.connect("data/db/片区库.sqlite3")
c.row_factory = sqlite3.Row
reg = {r["region_code"]: r["name"] for r in c.execute("select region_code,name from region")}

rows = c.execute("""
  select a.area_id, a.name, a.province_code, a.city_code, a.county_code, a.founded_ymd,
         a.founded_precision, a.status, a.type_code, a.scale_villages,
         x.caliber_group g, x.in_main_stat m,
         (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel in ('primary','support')) npol,
         (select s.publisher from area_source_map sm join source s on s.source_id=sm.source_id
            where sm.area_id=a.area_id limit 1) pub,
         (select s.credibility from area_source_map sm join source s on s.source_id=sm.source_id
            where sm.area_id=a.area_id order by case s.credibility when 'A' then 1 when 'B' then 2 else 3 end limit 1) cred,
         (select s.local_path from area_source_map sm join source s on s.source_id=sm.source_id
            where sm.area_id=a.area_id limit 1) snap
  from area a left join area_caliber x on x.area_id=a.area_id
  where a.record_state='active' and a.founded_ymd like '2021%'
  order by a.province_code, a.founded_ymd, a.area_id""").fetchall()

print(f"2021 年成立：{len(rows)} 条\n")
lines = ["| # | area_id | 名称 | 省/县 | 成立 | 状态 | 组 | 依据 | 来源 | 年份出处 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
for i, r in enumerate(rows, 1):
    prov = reg.get(r["province_code"], "")
    county = reg.get(r["county_code"], "")
    # 年份出处
    origin = "无快照"
    if r["snap"]:
        p = Path(r["snap"])
        if p.exists():
            t = p.read_text(encoding="utf-8")
            idx = t.find("2021")
            if idx < 0:
                origin = "快照无「2021」"
            else:
                seg = t[max(0, idx - 40): idx + 50].replace("\n", " ")
                origin = "快照有 2021" if not any(k in seg for k in ("ICP", "备案", "许可")) else "疑似备案号"
    print(f"{i:02d} {r['area_id']} {r['name']}｜{prov}{county}｜{r['founded_ymd']}｜{r['status']}｜"
          f"{r['g']}｜依据{r['npol']}｜{r['pub']}（{r['cred']}）｜{origin}")
    lines.append(f"| {i} | {r['area_id']} | {r['name']} | {prov}·{county} | {r['founded_ymd']} | "
                 f"{r['status']} | {r['g']} | {r['npol']} | {r['pub'] or '—'}（{r['cred'] or '—'}） | {origin} |")

out = Path("reports/qa/2021年成立片区-清单.md")
out.write_text("# 2021 年成立片区清单\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
print("\n->", out)
