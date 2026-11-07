import sys, re, importlib.util, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

url = sys.argv[1]
kws = sys.argv[2:] or ["片区", "组团", "重点村"]
try:
    h = t.fetch(url)
except Exception as e:
    print("ERR", e); sys.exit(0)
ls = t.links(h, url)
arts = [(href, txt) for href, txt in ls if re.search(r"/art/|\.html|\.shtml|\.htm", href)]
hit = [(href, txt) for href, txt in arts if any(k in txt for k in kws)]
print(f"[page {url}] links={len(ls)} articles={len(arts)} hits={len(hit)}")
seen = set()
for href, txt in hit:
    if href in seen:
        continue
    seen.add(href)
    print(f"  {href}\t{txt[:110]}")
