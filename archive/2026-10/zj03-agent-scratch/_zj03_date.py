import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"D:\CODEX\全国乡村片区化数据库\data\stage\POL-ZJ03-policy.jsonl"
for l in open(p, encoding="utf-8"):
    r = json.loads(l)
    t = r["full_text"]
    # 文末 400 字内的成文日期
    tail = t[-400:]
    m = re.findall(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", tail)
    cand = ""
    if m:
        y, mo, d = m[-1]
        cand = f"{y}-{int(mo):02d}-{int(d):02d}"
    flag = ""
    if cand and cand != r["issued_ymd"]:
        flag = f"  << 落款={cand} vs issued={r['issued_ymd'] or '(空)'}"
    print(f"{r['title'][:44]:44s} issued={r['issued_ymd'] or '(空)':10s} 落款={cand or '-':10s}{flag}")
