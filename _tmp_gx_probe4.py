from _tmp_gx_probe import get
urls = [
    'http://czt.gxzf.gov.cn/',
    'http://www.gxzf.gov.cn/zwgk/zfwj/',
    'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntf/',
    'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntgg/',
]
for u in urls:
    try:
        s, b = get(u, timeout=30)
        print(u, 'OK', s, len(b))
    except Exception as e:
        print(u, 'ERR', type(e).__name__, str(e)[:100])
