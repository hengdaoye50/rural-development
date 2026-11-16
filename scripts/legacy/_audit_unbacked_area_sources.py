"""审计「无政策依据」片区的名字来源：first_source_id 指向的发布者是政府还是媒体。

若大量片区的唯一来源是媒体（非 .gov.cn），则这些片区名不满足证据制准入，
需在统计口径里单列或标记待核。
"""
import csv
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

# 无 primary/support 依据的片区
rows = conn.execute("""
    SELECT a.area_id, a.name, a.province_code, a.county_code, a.first_source_id
    FROM area a
    WHERE a.record_state='active'
      AND NOT EXISTS (SELECT 1 FROM area_policy_map m
                      WHERE m.area_id=a.area_id AND m.rel IN ('primary','support'))
""").fetchall()
print(f"无 primary/support 依据的片区：{len(rows)}")

MEDIA = ("日报", "晚报", "商报", "新闻网", "新华", "人民网", "央视", "中新", "澎湃",
         "搜狐", "新浪", "腾讯", "网易", "凤凰", "界面", "大众网", "中国网", "光明网",
         "经济网", "融媒", "客户端", "公众号", "头条")

gov, media, unknown, nosrc = Counter(), [], [], []
src_cache = {}
for r in rows:
    sid = (r["first_source_id"] or "").strip()
    if not sid:
        nosrc.append(r)
        continue
    if sid not in src_cache:
        s = conn.execute(
            "SELECT url, publisher, title, credibility FROM source WHERE source_id=?", (sid,)
        ).fetchone()
        src_cache[sid] = s
    s = src_cache[sid]
    if not s:
        unknown.append(r)
        continue
    url = (s["url"] or "")
    pub = (s["publisher"] or "")
    if re.search(r"\.gov\.cn", url):
        gov[(r["province_code"],)] += 1
    else:
        hit = next((m for m in MEDIA if m in pub or m in url), "")
        media.append((r["area_id"], r["name"], r["province_code"], pub[:26],
                      (hit or "非gov站点"), url[:50]))

print(f"  来源为 .gov.cn：{sum(gov.values())}")
print(f"  来源非 .gov.cn：{len(media)}")
print(f"  source 行缺失：{len(unknown)}   无 first_source_id：{len(nosrc)}")

print(f"\n=== 来源非 .gov.cn 的片区（{len(media)} 个，按省）===")
byprov = Counter(m[2] for m in media)
for p, n in byprov.most_common():
    print(f"  {p} {n}")
print("\n样例：")
for m in media[:14]:
    print(f"  {m[0]} {m[1][:26]:<28} {m[3]:<26} [{m[4]}]")
