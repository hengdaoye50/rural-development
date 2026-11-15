"""Ad-hoc fetch helper: GET a URL and print status/len, optionally save to file."""
import sys, urllib.request, urllib.parse, gzip, io, ssl

def fetch(url, timeout=40, headers=None):
    h = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            raw = gzip.decompress(raw)
        return r.status, raw

def decode(raw, ctype=''):
    for enc in ('utf-8', 'gb18030', 'gbk'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')

if __name__ == '__main__':
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        st, raw = fetch(url)
    except Exception as e:
        print('ERR', type(e).__name__, e)
        sys.exit(1)
    txt = decode(raw)
    print('STATUS', st, 'BYTES', len(raw))
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(txt)
        print('SAVED', out, len(txt))
    else:
        print(txt[:4000])
