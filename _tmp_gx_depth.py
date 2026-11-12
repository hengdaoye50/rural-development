import re, io, sys
from _tmp_gx_probe import get

def probe(u, label):
    try:
        s, b = get(u, timeout=30)
    except Exception as e:
        print(label, 'ERR', str(e)[:90])
        return
    html = b.decode('utf-8', errors='replace')
    dates = re.findall(r'(20\d\d-\d\d-\d\d)', html)
    pages = re.findall(r'createPageHTML\(([^)]*)\)', html)
    print(label, 'len', len(html), 'pages', pages[:1], 'dates', (min(dates), max(dates)) if dates else None, 'n', len(dates))

for base in ['http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntf/',
             'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntgg/',
             'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/',
             'http://czt.gxzf.gov.cn/zfxxgkzl/zcwj/']:
    probe(base, base)
