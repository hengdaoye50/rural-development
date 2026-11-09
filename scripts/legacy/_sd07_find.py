import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
url = sys.argv[1]
pat = sys.argv[2]
raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
for enc in ('utf-8', 'gb18030'):
    h = raw.decode(enc, 'ignore')
    if h.count('\ufffd') < 20:
        break
for m in re.finditer(pat, h, re.I):
    s = max(0, m.start() - 120)
    print('...', h[s:m.end() + 160].replace('\n', ' '), '\n')
