import sys, re, html, urllib.parse
from _tmp_web import get, dec

q = sys.argv[1]
p = sys.argv[2] if len(sys.argv) > 2 else '1'
url = ('https://www.jiangsu.gov.cn/jsearchfront/search.do?' + urllib.parse.urlencode(
    {'q': q, 'websiteid': '320000000100000', 'searchid': '12', 'p': p, 'tpl': '38', 'sortType': '0'}))
st, raw = get(url)
t = dec(raw)
print('STATUS', st, 'LEN', len(t))
# result links often wrapped in visit/link.do?url=<encoded>
urls = re.findall(r'visit/link\.do\?url=([^"\'\s&]+)', t)
seen = []
for u in urls:
    d = urllib.parse.unquote(u)
    if d not in seen:
        seen.append(d)
rows = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', t, re.S)
ti = []
for u, x in rows:
    x = html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
    if len(x) >= 6:
        ti.append(x)
print('--- titles')
for i, x in enumerate(ti[:40], 1):
    print(i, x[:130])
print('--- decoded urls')
for u in seen[:40]:
    print(u)
