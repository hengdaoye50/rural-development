import re, io
from _tmp_gx_probe import get

s, b = get('http://www.gxzf.gov.cn/')
html = b.decode('utf-8', errors='replace')
io.open('_tmp_gxzf_home.html', 'w', encoding='utf-8').write(html)
print('gxzf home', s, len(html))
for pat in [r'action="([^"]*search[^"]*)"', r'href="([^"]*search[^"]*)"', r'(https?://[^"\' ]*search[^"\' ]*)']:
    for m in sorted(set(re.findall(pat, html)))[:20]:
        print('  search-ref:', m)

print('--- tzgg index_24 dates/titles ---')
s2, b2 = get('http://nynct.gxzf.gov.cn/xxgk/jcxxgk/tzgg/index_24.shtml')
h2 = b2.decode('utf-8', errors='replace')
for h, t in re.findall(r'<a[^>]+href="([^"]+/t\d+\.shtml)"[^>]*>\s*([^<]{6,90}?)\s*</a>', h2):
    print(' ', t, '|', h)
for d in re.findall(r'(20\d\d-\d\d-\d\d)', h2)[:25]:
    print('  date:', d)
