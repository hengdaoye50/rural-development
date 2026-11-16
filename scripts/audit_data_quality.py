"""数据质量与结构全量评估（只读）。

五个维度：
  A 表结构与体量
  B 必填字段填充率与口径一致性
  C 实体可信度分层（片区由哪一级文件的证据支撑）
  D 分省三角：片区数 / 政策数 / 覆盖率
  E 完整性与一致性（孤儿、重复、rel 分布、事件覆盖）
"""
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
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

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row


def scalar(sql, args=()):
    return conn.execute(sql, args).fetchone()[0]


def hdr(t):
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


n_area = scalar("SELECT COUNT(*) FROM area WHERE record_state='active'")
n_belt = scalar("SELECT COUNT(*) FROM belt WHERE record_state='active'")
n_pol = scalar("SELECT COUNT(*) FROM policy")

hdr("A. 表结构与体量")
for t in ("area", "belt", "policy", "source", "event", "area_policy_map",
          "area_region_map", "area_source_map", "belt_region_map", "region"):
    print(f"  {t:<18}{scalar(f'SELECT COUNT(*) FROM {t}'):>7}")

hdr("B. 字段填充率（area，active %d 条）" % n_area)
for col in ("founded_ymd", "cover_desc", "issuer", "lead_org", "town_codes",
            "scale_villages", "type_primary_note", "summary", "first_source_id"):
    n = scalar(f"SELECT COUNT(*) FROM area WHERE record_state='active' "
               f"AND {col} IS NOT NULL AND {col} != ''")
    print(f"  {col:<22}{n:>5}  ({n / n_area * 100:>3.0f}%)")

print("\n  founded_precision：",
      dict((r["p"], r["n"]) for r in conn.execute(
          "SELECT founded_precision p, COUNT(*) n FROM area "
          "WHERE record_state='active' GROUP BY p")))

print(f"\n  policy 关键字段（共 {n_pol} 条）：")
for col in ("doc_no", "issued_ymd", "instruments", "summary", "budget_wan",
            "target_areas", "county_code", "scope_desc"):
    n = scalar(f"SELECT COUNT(*) FROM policy WHERE {col} IS NOT NULL AND {col} != ''")
    print(f"  {col:<22}{n:>5}  ({n / n_pol * 100:>3.0f}%)")

hdr("B2. 口径一致性（已知问题复查）")
kinds = Counter()
for r in conn.execute("SELECT town_codes t FROM area WHERE record_state='active'"):
    t = (r["t"] or "").strip()
    if not t:
        kinds["空"] += 1
    elif re.fullmatch(r"\d{9}", t):
        kinds["九位乡镇码"] += 1
    elif re.search(r"[\u4e00-\u9fa5]", t):
        kinds["中文乡镇名"] += 1
    else:
        kinds["其它/垃圾值"] += 1
for k, v in kinds.most_common():
    print(f"  town_codes {k:<14}{v}")

bad_scale = scalar(
    "SELECT COUNT(*) FROM area WHERE record_state='active' AND scale_villages != '' "
    "AND CAST(scale_villages AS INTEGER) = 0")
print(f"  scale_villages 非数字或为 0：{bad_scale}")

hdr("C. 实体可信度分层：片区的证据来自哪一级文件")
grade = Counter()
for r in conn.execute("""
    SELECT a.area_id,
           MAX(CASE p.issuer_level WHEN 'province' THEN 3 WHEN 'city' THEN 2
                                   WHEN 'county' THEN 1 ELSE 0 END) lv,
           COUNT(m.policy_id) n
    FROM area a
    LEFT JOIN area_policy_map m ON m.area_id = a.area_id AND m.rel IN ('primary','support')
    LEFT JOIN policy p ON p.policy_id = m.policy_id
    WHERE a.record_state='active'
    GROUP BY a.area_id
"""):
    if r["n"] == 0:
        grade["无任何政策依据"] += 1
    elif r["lv"] >= 3:
        grade["省级文件"] += 1
    elif r["lv"] == 2:
        grade["市级文件"] += 1
    elif r["lv"] == 1:
        grade["县级文件"] += 1
    else:
        grade["镇级/其他"] += 1
for k, v in grade.most_common():
    print(f"  {k:<18}{v:>5}  ({v / n_area * 100:>3.0f}%)")

print("\n  type_code 分布：",
      dict((r["t"], r["n"]) for r in conn.execute(
          "SELECT type_code t, COUNT(*) n FROM area WHERE record_state='active' "
          "GROUP BY t ORDER BY n DESC")))

hdr("D. 分省三角：片区数 / 有依据 / 覆盖率 / 政策数 / 政策÷片区")
rows = conn.execute("""
    SELECT a.province_code p, COUNT(*) n,
           SUM(CASE WHEN m.area_id IS NOT NULL THEN 1 ELSE 0 END) cov
    FROM area a
    LEFT JOIN (SELECT DISTINCT area_id FROM area_policy_map) m ON m.area_id = a.area_id
    WHERE a.record_state='active' GROUP BY a.province_code
""").fetchall()
pol = {r["p"]: r["n"] for r in conn.execute(
    "SELECT province_code p, COUNT(*) n FROM policy GROUP BY p")}
print(f"  {'省':<7}{'片区':>5}{'有依据':>7}{'覆盖率':>7}{'政策':>6}{'政策/片区':>10}")
for r in sorted(rows, key=lambda x: -x["n"]):
    p, n, cov = r["p"], r["n"], r["cov"]
    npo = pol.get(p, 0)
    print(f"  {PROV.get(p, p):<7}{n:>5}{cov:>7}{cov / n * 100:>6.0f}%{npo:>6}{npo / n:>10.1f}")

hdr("E. 完整性与一致性")
print("  area_policy_map rel 分布：",
      dict((r["rel"], r["n"]) for r in conn.execute(
          "SELECT rel, COUNT(*) n FROM area_policy_map GROUP BY rel ORDER BY n DESC")))
print(f"  area 有 region 映射：  {scalar('SELECT COUNT(DISTINCT area_id) FROM area_region_map')}/{n_area}")
print(f"  area 有 event：        {scalar('SELECT COUNT(DISTINCT area_id) FROM event')}/{n_area}")
n_firstsrc = scalar(
    "SELECT COUNT(*) FROM area WHERE record_state=? AND first_source_id IS NOT NULL "
    "AND first_source_id != ?", ("active", ""))
print(f"  area 有 first_source： {n_firstsrc}/{n_area}")
print(f"  policy 缺 local_path： {scalar('SELECT COUNT(*) FROM policy WHERE local_path IS NULL OR local_path = ?', ('',))}")
print(f"  source 无快照：        {scalar('SELECT COUNT(*) FROM source WHERE local_path IS NULL OR local_path = ?', ('',))}/{scalar('SELECT COUNT(*) FROM source')}")
print(f"  belt 有 region 映射：  {scalar('SELECT COUNT(DISTINCT belt_id) FROM belt_region_map')}/{n_belt}")

dups = conn.execute("""
    SELECT county_code, name, COUNT(*) n FROM area WHERE record_state='active'
    GROUP BY county_code, name HAVING n > 1
""").fetchall()
print(f"  area 同县同名重复：    {len(dups)} 组" +
      ("" if not dups else "：" + "；".join(f"{d['county_code']} {d['name']}×{d['n']}" for d in dups[:5])))
