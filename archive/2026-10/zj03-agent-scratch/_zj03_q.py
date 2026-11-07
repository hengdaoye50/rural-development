import sys, json, re, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("a", D + r"\_zj03_api.py")
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

wid = sys.argv[1]
q = sys.argv[2]
pg = int(sys.argv[3]) if len(sys.argv) > 3 else 20
d = a.search(wid, q, pg, 1)
bl = (d.get("data") or {}).get("appSearchResultBeanList") or []
tot = 0
for b in bl:
    msr = b.get("mapSearchResult") or {}
    tot += msr.get("total") or 0
    for it in (msr.get("items") or []):
        dd = it.get("data") or {}
        dt = ""
        if dd.get("createdate"):
            try:
                dt = datetime.datetime.fromtimestamp(int(dd["createdate"]) / 1000,
                                                    datetime.timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
        print(f"{dt} | {dd.get('module','')[:12]:12s} | {dd.get('webname','')[:16]:16s} | {(dd.get('title_h') or '')[:62]}")
        print(f"      {dd.get('url')}")
print(f"[total~{tot}]")
