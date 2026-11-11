"""统计报告取数：把分析所需的口径一次性算出来（只读）。

用法：python scripts/_analysis_probe.py
"""
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def hdr(t):
    print(f"\n{'='*66}\n{t}\n{'='*66}")


hdr("1. 命名形态：片区名的构词")
forms = {
    "含「片区」": "%片区%", "含「示范带」": "%示范带%", "含「组团」": "%组团%",
    "含「示范片」": "%示范片%", "含「片区/示范带」均有": "%片区%示范带%",
    "含「群」": "%群%", "含「群落」": "%群落%", "含「发展轴」": "%发展轴%",
    "含「联合体/联盟」": "%联%",
}
n = conn.execute("SELECT COUNT(*) FROM area WHERE record_state='active'").fetchone()[0]
print(f"片区总数 {n}")
for label, pat in forms.items():
    c = conn.execute(
        "SELECT COUNT(*) FROM area WHERE record_state='active' AND name LIKE ?", (pat,)
    ).fetchone()[0]
    print(f"  {label:<22}{c:>5}  ({c/n*100:.0f}%)")

hdr("2. 谁在命名：挂到 each area 的 primary 政策的发文层级")
rows = conn.execute(
    """
    SELECT a.province_code p, p.issuer_level lv, COUNT(DISTINCT m.area_id) n
    FROM area_policy_map m
    JOIN area a ON a.area_id=m.area_id
    JOIN policy p ON p.policy_id=m.policy_id
    WHERE m.rel='primary' AND a.record_state='active'
    GROUP BY a.province_code, p.issuer_level
    """
).fetchall()
by_prov = defaultdict(Counter)
for r in rows:
    by_prov[r["p"]][r["lv"]] += r["n"]
print("按省：primary 依据的发文层级分布（省级/市级/县级/镇级）")
for p, c in sorted(by_prov.items(), key=lambda x: -sum(x[1].values()))[:15]:
    tot = sum(c.values())
    print(f"  {PROV.get(p, p):<5} 省{c.get('province',0):>3} 市{c.get('city',0):>3} "
          f"县{c.get('county',0):>3} 镇{c.get('town',0):>2}   共 {tot}")

hdr("3. 资金：原文明确写出的片区资金规模")
q = conn.execute(
    "SELECT COUNT(*) n, SUM(budget_wan) s, MIN(budget_wan) mn, MAX(budget_wan) mx "
    "FROM policy WHERE budget_wan IS NOT NULL AND budget_wan != ''"
).fetchone()
print(f"有 budget_wan 的政策 {q['n']} 条，合计 {q['s'] or 0:,.0f} 万元 "
      f"(约 {(q['s'] or 0)/10000:,.1f} 亿元)，单条区间 {q['mn']:,} – {q['mx']:,} 万元")

hdr("4. 片区成立年份（有精度记录的）")
for r in conn.execute(
    "SELECT SUBSTR(founded_ymd,1,4) y, COUNT(*) n FROM area "
    "WHERE record_state='active' AND founded_ymd IS NOT NULL AND founded_ymd!='' "
    "GROUP BY y ORDER BY y"
):
    print(f"  {r['y']}  {r['n']}")

hdr("5. 考核/验收类政策：instruments 里出现哪些机制词")
mech = ["考核", "验收", "评估", "排名", "奖补", "以奖代补", "竞争性", "遴选",
        "负面清单", "退出", "动态调整", "摘牌"]
for m in mech:
    c = conn.execute(
        "SELECT COUNT(*) FROM policy WHERE instruments LIKE ?", (f"%{m}%",)
    ).fetchone()[0]
    if c:
        print(f"  {m:<10}{c}")

hdr("6. 组织形态：instruments 中的组织类提法")
org = ["片区党委", "联合党委", "片区党总支", "党建联合体", "联村", "专班",
       "领导小组", "强村公司", "片区组团", "组团式"]
for o in org:
    c = conn.execute(
        "SELECT COUNT(*) FROM policy WHERE instruments LIKE ?", (f"%{o}%",)
    ).fetchone()[0]
    if c:
        print(f"  {o:<12}{c}")

hdr("7. 覆盖率最高的省 vs 最低的省")
rows = conn.execute(
    """
    SELECT a.province_code p, COUNT(*) n,
           SUM(CASE WHEN m.area_id IS NOT NULL THEN 1 ELSE 0 END) cov
    FROM area a
    LEFT JOIN (SELECT DISTINCT area_id FROM area_policy_map) m ON m.area_id=a.area_id
    WHERE a.record_state='active' GROUP BY a.province_code
    """
).fetchall()
rank = sorted(((PROV.get(r["p"], r["p"]), r["cov"], r["n"]) for r in rows),
              key=lambda x: -(x[1] / x[2] if x[2] else 0))
print("  最高：" + "、".join(f"{p} {c}/{t}（{c/t*100:.0f}%）" for p, c, t in rank[:6]))
print("  最低：" + "、".join(f"{p} {c}/{t}（{c/t*100:.0f}%）" for p, c, t in rank[-6:]))
