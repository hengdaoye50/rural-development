import csv, io, sys, re
sys.stdout.reconfigure(encoding="utf-8")

rows = list(csv.DictReader(io.open("reports/qa/link-veracity.csv", encoding="utf-8-sig")))
miss = [r for r in rows if r["tier"] == "missing"]
print("missing 链接", len(miss))

# 各挑几条，去原文里搜核心词，看是真没有还是判据问题
probes = [
    ("A370114", "红韵崔口片区", "崔口"),
    ("A210006", "庄河市光明山版乡村振兴示范带", "光明山"),
    ("A330004", "嘉兴市南湖区大三星片区", "大三星"),
    ("A320017", "宜南茶乡竹海山水画廊片区", "宜南"),
    ("A520004", "陈家组片区（玉屏亚鱼）", "亚鱼"),
    ("A440023", "粤湘廊道·南岭明珠乡村振兴示范带", "南岭"),
]
for aid, aname, kw in probes:
    hits = [r for r in miss if r["area_id"] == aid]
    if not hits:
        print(f"\n{aid} 不在 missing 里")
        continue
    r = hits[0]
    try:
        t = io.open(r["local_path"], encoding="utf-8", errors="ignore").read()
    except OSError as e:
        print(f"\n{aid} 读不到 {r['local_path']} {e}")
        continue
    compact = re.sub(r"\s+", "", t)
    print(f"\n===== {aid} 「{aname}」 搜「{kw}」 len={len(compact)}")
    print(f"  policy {r['policy_id']} {r['policy_title']}")
    for m in list(re.finditer(re.escape(kw), compact))[:3]:
        print("   ...", compact[max(0, m.start()-40): m.start()+60])
    if kw not in compact:
        # 试单字
        for ch in kw:
            print(f"    单字「{ch}」出现 {compact.count(ch)} 次")
        print("   >>> 关键词确实不在正文")
