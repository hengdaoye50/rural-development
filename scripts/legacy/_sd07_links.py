import urllib.request, re, sys
sys.stdout.reconfigure(encoding='utf-8')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'}
url = sys.argv[1]
kw = sys.argv[2].split(',') if len(sys.argv) > 2 else ['规划', '政策', '报告', '公报']
raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
h = raw.decode('utf-8', 'ignore')
if '锟' in h or h.count('\ufffd') > 50:
    h = raw.decode('gb18030', 'ignore')
seen = set()
for href, txt in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{2,24})\s*</a>', h):
    txt = txt.strip()
    if any(k in txt for k in kw) and txt not in seen:
        seen.add(txt)
        print(txt, '->', href)
