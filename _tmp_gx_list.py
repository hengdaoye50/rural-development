import re, io, sys
from _tmp_gx_probe import get

u = sys.argv[1] if len(sys.argv) > 1 else 'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/tzgg/'
status, b = get(u)
html = b.decode('utf-8', errors='replace')
print('status', status, 'len', len(html))
print('--- title:', re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip() if re.search(r'<title>(.*?)</title>', html, re.S) else '?')
items = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,90}?)\s*</a>', html)
for h, t in items:
    if re.search(r'/t\d+\.s?html', h):
        print(t, '->', h)
print('--- pagination hints ---')
for m in set(re.findall(r'(index_\d+\.s?html|createPageHTML[^;]{0,120}|countPage[^;]{0,80}|maxPage[^;]{0,40})', html)):
    print(m)
