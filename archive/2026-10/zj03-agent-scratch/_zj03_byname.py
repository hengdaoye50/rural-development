import sys, json, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("a", D + r"\_zj03_api.py")
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
wid = sys.argv[1]
for name in sys.argv[2:]:
    d = a.search(wid, name, 10, 1)
    bl = (d.get("data") or {}).get("appSearchResultBeanList") or []
    hits = []
    for b in bl:
        for it in ((b.get("mapSearchResult") or {}).get("items") or []):
            dd = it.get("data") or {}
            hits.append((dd.get("createdate"), (dd.get("title_h") or "")[:56], dd.get("url"), dd.get("webname")))
    print(f"\n### {name}  hits={len(hits)}")
    for c, t, u, w in hits[:8]:
        dt = ""
        if c:
            try:
                dt = datetime.datetime.fromtimestamp(int(c) / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
        print(f"  {dt} | {w} | {t}\n      {u}")
