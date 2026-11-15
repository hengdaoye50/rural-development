"""POST/GET helper for gov site searches."""
import sys, urllib.request, urllib.parse, gzip, ssl, re

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

def _open(req, timeout=40):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            raw = gzip.decompress(raw)
        return r.status, raw

def get(url, headers=None, timeout=40):
    h = {'User-Agent': UA, 'Accept-Language': 'zh-CN,zh;q=0.9'}
    if headers: h.update(headers)
    return _open(urllib.request.Request(url, headers=h), timeout)

def post(url, data, headers=None, timeout=40):
    h = {'User-Agent': UA, 'Accept-Language': 'zh-CN,zh;q=0.9',
         'Content-Type': 'application/x-www-form-urlencoded'}
    if headers: h.update(headers)
    body = urllib.parse.urlencode(data).encode('utf-8')
    return _open(urllib.request.Request(url, data=body, headers=h), timeout)

def dec(raw):
    for enc in ('utf-8', 'gb18030'):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode('utf-8', 'replace')

if __name__ == '__main__':
    mode = sys.argv[1]
    url = sys.argv[2]
    if mode == 'post':
        data = dict(kv.split('=', 1) for kv in sys.argv[3:] if '=' in kv)
        st, raw = post(url, data)
    else:
        st, raw = get(url)
    t = dec(raw)
    print('STATUS', st, 'BYTES', len(raw))
    print(t[:6000])
