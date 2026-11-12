"""数据完整性盘点：按层、按口径给出缺口清单。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

PROV = {
    "110000": "北京", "120000": "天津", "130000": "河北", "140000": "山西",
    "150000": "内蒙古", "210000": "辽宁", "220000": "吉林", "230000": "黑龙江",
    "310000": "上海", "320000": "江苏", "330000": "浙江", "340000": "安徽",
    "350000": "福建", "360000": "江西", "370000": "山东", "410000": "河南",
    "420000": "湖北", "430000": "湖南", "440000": "广东", "450000": "广西",
    "460000": "海南", "500000": "重庆", "510000": "四川", "520000": "贵州",
    "530000": "云南", "540000": "西藏", "610000": "陕西", "620000": "甘肃",
    "630000": "青海", "640000": "宁夏", "650000": "新疆",
}

print("=== 1. 片区层：各省片区数（判断厚度）===")
rows = conn.execute(
    "SELECT province_code p, COUNT(*) n FROM area WHERE record_state='active' "
    "GROUP BY p ORDER BY n"
).fetchall()
thin = [r for r in rows if r["n"] <= 8]
print(f"31 省合计 {sum(r['n'] for r in rows)}；片区数 ≤8 的省 {len(thin)} 个：")
for r in thin:
    print(f"  {PROV.get(r['p'], r['p']):<5}{r['n']}")

print("\n=== 2. 政策层：未覆盖片区 by 省 ===")
un = conn.execute(
    """
    SELECT a.province_code p, COUNT(*) n FROM area a
    WHERE a.record_state='active'
      AND a.area_id NOT IN (SELECT area_id FROM area_policy_map)
    GROUP BY a.province_code ORDER BY n DESC
    """
).fetchall()
print(f"合计未覆盖 {sum(r['n'] for r in un)}")
for r in un[:8]:
    print(f"  {PROV.get(r['p'], r['p']):<5}{r['n']}")

print("\n=== 3. 严格口径：只有 mention 支撑的片区 by 省 ===")
mo = conn.execute(
    """
    SELECT a.province_code p, COUNT(*) n FROM area a
    WHERE a.record_state='active'
      AND EXISTS (SELECT 1 FROM area_policy_map m
                  WHERE m.area_id=a.area_id AND m.rel='mention')
      AND NOT EXISTS (SELECT 1 FROM area_policy_map m2
                      WHERE m2.area_id=a.area_id AND m2.rel IN ('primary','support'))
    GROUP BY a.province_code ORDER BY n DESC
    """
).fetchall()
print(f"合计 {sum(r['n'] for r in mo)}")
for r in mo[:6]:
    print(f"  {PROV.get(r['p'], r['p']):<5}{r['n']}")

print("\n=== 4. 时间覆盖：政策成文年份占比 ===")
tot = conn.execute("SELECT COUNT(*) FROM policy").fetchone()[0]
y = {}
for r in conn.execute("SELECT issued_ymd v FROM policy WHERE issued_ymd LIKE '____%-%'"):
    y[r["v"][:4]] = y.get(r["v"][:4], 0) + 1
after = sum(v for k, v in y.items() if k >= "2022")
print(f"  政策 {tot} 条；有合法成文日期 {sum(y.values())} 条；2022 年及以后 {after} 条 "
      f"（占有日期的 {after/sum(y.values())*100:.0f}%）")

print("\n=== 5. 证据链 ===")
print(f"  policy 全文存档：{conn.execute('SELECT COUNT(*) FROM policy WHERE local_path != \"\"').fetchone()[0]}/{tot}")
print(f"  budget_wan 有值：{conn.execute('SELECT COUNT(*) FROM policy WHERE budget_wan IS NOT NULL AND budget_wan != \"\"').fetchone()[0]}")
print(f"  target_areas 有值：{conn.execute('SELECT COUNT(*) FROM policy WHERE target_areas IS NOT NULL AND target_areas != \"\"').fetchone()[0]}")
print(f"  source 有快照：{conn.execute('SELECT COUNT(*) FROM source WHERE local_path IS NOT NULL AND local_path != \"\"').fetchone()[0]}/"
      f"{conn.execute('SELECT COUNT(*) FROM source').fetchone()[0]}")
raw_pdf = list((ROOT / "data" / "raw").rglob("原件.pdf"))
raw_doc = list((ROOT / "data" / "raw").rglob("原件.doc"))
print(f"  原件存档：pdf {len(raw_pdf)} / doc {len(raw_doc)}（存量缺口按 docs/03 不追溯）")

print("\n=== 6. 片区字段填充率 ===")
for col in ("founded_ymd", "scale_villages", "cover_desc", "issuer", "lead_org", "town_codes"):
    n = conn.execute(
        f"SELECT COUNT(*) FROM area WHERE record_state='active' AND {col} IS NOT NULL AND {col} != ''"
    ).fetchone()[0]
    print(f"  {col:<16}{n}/1038  ({n/1038*100:.0f}%)")

print("\n=== 7. 事件层 ===")
print(f"  event {conn.execute('SELECT COUNT(*) FROM event').fetchone()[0]} 条，"
      f"覆盖 {conn.execute('SELECT COUNT(DISTINCT area_id) FROM event WHERE area_id != \"\"').fetchone()[0]} 个片区")
