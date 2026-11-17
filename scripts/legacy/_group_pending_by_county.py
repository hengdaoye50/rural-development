"""待核片区按县归并 + 原有待核归因。

用途 1：看哪些县有多个待核片区——这些县值得抓一份县级名单/发展轴规划，
        一份文件能覆盖多个片区，比「按片区逐个搜」高效一个量级。
用途 2：区分「本脚本标记的待核」（媒体来源）与「原有待核」（原因各不同）。
"""
import csv
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

county_name = {r["region_code"]: r["name"] for r in conn.execute(
    "SELECT region_code, name FROM region WHERE length(region_code)=6")}
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

rows = conn.execute("""
    SELECT a.area_id, a.name, a.province_code, a.county_code, a.summary,
           s.url, s.publisher, s.credibility
    FROM area a LEFT JOIN source s ON s.source_id = a.first_source_id
    WHERE a.record_state='active' AND a.status='待核'
    ORDER BY a.province_code, a.county_code, a.area_id
""").fetchall()

marked = [r for r in rows if "【证据待核】" in (r["summary"] or "")]
original = [r for r in rows if "【证据待核】" not in (r["summary"] or "")]
print(f"待核合计 {len(rows)}：本脚本标记 {len(marked)}，原有 {len(original)}\n")

print("=== 原有待核归因（{0} 条）===".format(len(original)))
reason = Counter()
for r in original:
    url = r["url"] or ""
    if not url:
        reason["无 source / 无 URL"] += 1
    elif ".gov.cn" in url:
        reason["有 .gov.cn 来源但未挂政策"] += 1
    else:
        reason["来源非 gov（未带标记）"] += 1
for k, v in reason.most_common():
    print(f"  {k:<28}{v}")
print("\n  样例：")
for r in original[:10]:
    print(f"    {r['area_id']} {r['name'][:26]:<28} src={r['publisher'] or r['url'][:30] or '无'}")

print(f"\n=== 按县归并：待核片区 ≥2 个的县（这些县一份文件可覆盖多个）===")
by_county = defaultdict(list)
for r in rows:
    by_county[(r["province_code"], r["county_code"])].append(r)
multi = sorted(((k, v) for k, v in by_county.items() if len(v) >= 2),
               key=lambda x: (-len(x[1]), x[0]))
print(f"  {'省':<6}{'县码':<9}{'县名':<12}{'待核数'}")
for (p, cc), items in multi[:25]:
    print(f"  {PROV.get(p, p):<6}{cc:<9}{county_name.get(cc, '?'):<12}{len(items)}")
print(f"\n  涉及 {len(multi)} 个县，共 {sum(len(v) for _, v in multi)} 个待核片区"
      f"（占全部待核 {sum(len(v) for _, v in multi) / len(rows) * 100:.0f}%）")
print(f"  其余 {len(by_county) - len(multi)} 个县各只有 1 个待核")
