import re, io
from _tmp_gx_probe import get

u = 'http://nynct.gxzf.gov.cn/xxgk/gkbz/zfxxgkml/'
s, b = get(u, timeout=30)
html = b.decode('utf-8', errors='replace')
io.open('_tmp_ml.html', 'w', encoding='utf-8').write(html)
print(s, len(html))
# forms / select options / ajax urls
for m in re.findall(r'<form[^>]*>', html):
    print('FORM', m)
for m in sorted(set(re.findall(r'(url\s*:\s*["\'][^"\']+["\'])', html))):
    print('AJAX', m)
for m in sorted(set(re.findall(r'(/[\w/\-]+\.(?:do|json|shtml))', html)))[:40]:
    print('PATH', m)
titles = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{4,80}?)\s*</a>', html)
for h, t in titles[:40]:
    print('LINK', t, '->', h)
