import sys, re, urllib.parse, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

q = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
url = "https://www.bing.com/search?q=" + urllib.parse.quote(q) + "&count=30&setlang=zh-CN"
h = t.fetch(url)
# Bing result anchors: <h2><a href="...">
seen = []
for m in re.finditer(r'(?is)<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', h):
    href, txt = m.group(1), t.strip(m.group(2)).replace("\n", " ")
    if href.startswith("https://www.bing.com") or href.startswith("/"):
        continue
    if href in [s[0] for s in seen]:
        continue
    seen.append((href, txt))
for i, (href, txt) in enumerate(seen[:n], 1):
    print(f"{i}. {txt}\n   {href}")
print(f"[total={len(seen)}]")
