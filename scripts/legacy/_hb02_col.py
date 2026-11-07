import re, sys, io, urllib.request, urllib.error

base = "http://nyt.hubei.gov.cn/bmdt/ztzl/zxzt/sdgjz/cyjzfp/"
hd = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
seen = {}
for i in range(0, 12):
    url = base + ("index.shtml" if i == 0 else "index_%d.shtml" % i)
    try:
        req = urllib.request.Request(url, headers=hd)
        raw = urllib.request.urlopen(req, timeout=30).read()
        try:
            html = raw.decode("utf-8")
        except UnicodeDecodeError:
            html = raw.decode("gbk", errors="replace")
    except Exception as e:
        print("FAIL", url, e, file=sys.stderr)
        continue
    found = 0
    for m in re.finditer(r'href="([^"]*t\d{8}_\d+(?:_slh)?\.shtml)"[^>]*>\s*([^<]{4,80})$', html, re.M):
        pass
    # generic: find <a href=... title="...">
    for m in re.finditer(r'<a[^>]+href="([^"]*t\d{8}_\d+(?:_slh)?\.shtml)"[^>]*title="([^"]{4,80})"', html):
        u, t = m.group(1), m.group(2).strip()
        if u not in seen:
            seen[u] = t
            found += 1
    print("page %d -> %d new" % (i, found), file=sys.stderr)

for u, t in seen.items():
    print(t, "|", u)
