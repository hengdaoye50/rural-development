import re, io
from _tmp_gx_probe import get

for u in ['http://www.gxzf.gov.cn/zddt/', 'http://nynct.gxzf.gov.cn/xxgk/zfxxgkzl/']:
    try:
        s, b = get(u, timeout=30)
    except Exception as e:
        print(u, 'ERR', e)
        continue
    html = b.decode('utf-8', errors='replace')
    name = '_tmp_' + re.sub(r'\W+', '_', u) + '.html'
    io.open(name, 'w', encoding='utf-8').write(html)
    print('==', u, s, len(html), '->', name)
    seen = set()
    for h, t in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{2,30}?)\s*</a>', html):
        t = t.strip()
        if any(k in t for k in ['政策', '文件', '公报', '公开', '通知', '公告', '公示']):
            if (t, h) in seen:
                continue
            seen.add((t, h))
            print('   ', t, '->', h)
