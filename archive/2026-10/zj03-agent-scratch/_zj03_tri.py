import sys, json, re, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("t", D + r"\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

cc = sys.argv[1]
kwf = sys.argv[2] if len(sys.argv) > 2 else "片区"
items = json.load(open(D + rf"\_zj03_raw\harvest-{cc}.json", encoding="utf-8"))
rows = []
for it in items:
    body = t.strip(it["vc_content"])
    n = len(re.findall(r"[\u4e00-\u9fff]", body))
    hits = body.count("片区")
    if kwf and kwf not in (it["title"] + body):
        continue
    d = ""
    if it.get("createdate"):
        try:
            d = datetime.datetime.utcfromtimestamp(int(it["createdate"]) / 1000).strftime("%Y-%m-%d")
        except Exception:
            pass
    rows.append((d, it["module"], n, hits, it["title"][:70], it["url"]))
rows.sort(reverse=True)
print(f"cc={cc} items={len(items)} filtered={len(rows)}")
for r in rows:
    print(f"{r[0]} | {r[1][:14]:14s} | {r[2]:5d}字 | 片区x{r[3]:2d} | {r[4]}")
