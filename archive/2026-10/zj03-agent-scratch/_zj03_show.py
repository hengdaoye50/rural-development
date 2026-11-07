import sys, json, glob, os
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_raw\txt"
ids = sys.argv[1:]
for i in ids:
    p = os.path.join(D, i + ".json")
    if not os.path.exists(p):
        print(f"--- {i} MISSING"); continue
    d = json.load(open(p, encoding="utf-8"))
    print(f"\n===== {i} | {d['title']} | {d['url']} | chars={d['chars']}")
    print(d["body_md"][:int(os.environ.get("MAXC", "1400"))])
