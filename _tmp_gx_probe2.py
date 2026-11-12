import sys
from _tmp_gx_probe import get

urls = [
    'http://nynct.gxzf.gov.cn/site/gxny/search.html',
    'http://www.gxzf.gov.cn/',
    'https://www.gxzf.gov.cn/',
    'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/tzgg/index_24.shtml',
    'http://nynct.gxzf.gov.cn/xxgk/zfxxgkzl/',
]
for u in urls:
    try:
        s, b = get(u, timeout=30)
        print(u, 'OK', s, len(b))
    except Exception as e:
        print(u, 'ERR', type(e).__name__, str(e)[:120])
