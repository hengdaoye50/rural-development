import sys, re, urllib.parse, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

q = sys.argv[1]
first = sys.argv[2] if len(sys.argv) > 2 else "1"
url = ("https://www.bing.com/search?q=" + urllib.parse.quote(q)
       + "&first=" + first + "&setlang=zh-CN&cc=CN")
h = t.fetch(url)
blocks = re.split(r'(?i)<li class="b_algo"', h)[1:]
if not blocks:
    print("NO b_algo; head sample:")
    print(h[:1500])
for i, b in enumerate(blocks, 1):
    m = re.search(r'(?is)<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b)
    if not m:
        m = re.search(r'(?is)<a[^>]*href="(http[^"]+)"[^>]*>(.*?)</a>', b)
    if not m:
        continue
    href = m.group(1).replace("&amp;", "&")
    mm = re.search(r"[?&]u=([^&]+)", href)
    if mm and mm.group(1).startswith("a1"):
        import base64
        s = mm.group(1)[2:]
        s += "=" * (-len(s) % 4)
        try:
            href = base64.urlsafe_b64decode(s).decode("utf-8", "ignore")
        except Exception:
            pass
    title = t.strip(m.group(2)).replace("\n", " ")
    snip = ""
    ms = re.search(r'(?is)<p[^>]*>(.*?)</p>', b)
    if ms:
        snip = t.strip(ms.group(1)).replace("\n", " ")[:220]
    print(f"{i}. {title}\n   {href}\n   {snip}")
print(f"[n={len(blocks)}]")
