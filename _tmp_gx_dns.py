import socket
from _tmp_gx_probe import get

for host in ['czt.gxzf.gov.cn', 'www.gxcz.gov.cn', 'gxny.gov.cn', 'www.gxny.gov.cn']:
    try:
        ip = socket.gethostbyname(host)
        print(host, 'DNS ->', ip)
    except Exception as e:
        print(host, 'DNS FAIL', type(e).__name__)

for u in ['http://czt.gxzf.gov.cn/xwdt/tzgg/', 'http://www.gxcz.gov.cn/', 'http://czt.gxzf.gov.cn/']:
    try:
        s, b = get(u, timeout=25)
        print(u, 'OK', s, len(b))
    except Exception as e:
        print(u, 'ERR', type(e).__name__, str(e)[:80])
