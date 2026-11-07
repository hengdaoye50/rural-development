import sys, json, importlib.util, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
spec2 = importlib.util.spec_from_file_location("a", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_api.py")
a = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(a)
d = a.search("330324000000", "片区组团", 3, 1)
bl = d["data"]["appSearchResultBeanList"]
print("nbean", len(bl))
for b in bl:
    print("cate:", b["category"]["categoryName"], "total:", (b.get("mapSearchResult") or {}).get("total"))
it = bl[0]["mapSearchResult"]["items"][0]
print("ITEM KEYS:", list(it.keys()))
print("DATA KEYS:", list(it["data"].keys()))
for k, v in it["data"].items():
    s = str(v)
    print(f"  {k} = {s[:120]}")
