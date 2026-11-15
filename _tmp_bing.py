"""Bing search helper: print result titles + urls."""
import sys, re, html, urllib.parse
from _tmp_fetch import fetch, decode

def bing(q, count=30, first=1):
    url = 'https://cn.bing.com/search?' + urllib.parse.urlencode({'q': q, 'count': count, 'first': first})
    st, raw = fetch(url)
    t = decode(raw)
    out = []
    for m in re.finditer(r'<li class="b_algo".*?</li>', t, re.S):
        blk = m.group(0)
        a = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not a:
            continue
        u = html.unescape(a.group(1))
        ti = re.sub(r'<[^>]+>', '', a.group(2))
        ti = html.unescape(ti).strip()
        cap = re.search(r'<p[^>]*>(.*?)</p>', blk, re.S)
        c = re.sub(r'<[^>]+>', '', cap.group(1)) if cap else ''
        c = html.unescape(c).strip()
        out.append((ti, u, c))
    return out

if __name__ == '__main__':
    q = sys.argv[1]
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    res = bing(q, cnt)
    print('N=', len(res))
    for i, (t, u, c) in enumerate(res, 1):
        print('[%d] %s' % (i, t))
        print('    %s' % u)
        print('    %s' % c[:220].replace('\n', ' '))
