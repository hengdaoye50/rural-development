import sys, re, html
from _tmp_web import post, get, dec

q = sys.argv[1]
site = sys.argv[2] if len(sys.argv) > 2 else '3211000002'
st, raw = post('https://www.zhenjiang.gov.cn/search4/s',
               {'searchWord': q, 'uc': '1', 'siteCode': site, 'column': '全部'})
t = dec(raw)
# find result blocks: links to /art/ or .shtml/.html with titles
rows = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', t, re.S)
seen = set()
for u, ti in rows:
    ti = re.sub(r'<[^>]+>', '', ti)
    ti = html.unescape(ti).strip()
    if len(ti) < 8:
        continue
    if q not in ti and '片区' not in ti:
        continue
    if u in seen:
        continue
    seen.add(u)
    print(ti[:120], '||', u)
