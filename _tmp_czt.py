import re, io
from _tmp_gx_probe import get

s, b = get('http://czt.gxzf.gov.cn/')
html = b.decode('utf-8', errors='replace')
io.open('_tmp_czt_home.html', 'w', encoding='utf-8').write(html)
print('czt home', s, len(html))
seen = set()
for h, t in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{2,40}?)\s*</a>', html):
    t = t.strip()
    if any(k in t for k in ['通知', '公告', '公示', '公开', '文件', '政策', '检索', '搜索', '名单']):
        if (t, h) in seen:
            continue
        seen.add((t, h))
        print(' ', t, '->', h)
