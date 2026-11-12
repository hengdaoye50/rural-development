import urllib.request, ssl, re, io, sys
ssl._create_default_https_context = ssl._create_unverified_context

def get(u, timeout=40):
    req = urllib.request.Request(u, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })
    r = urllib.request.urlopen(req, timeout=timeout)
    return r.status, r.read()

if __name__ == '__main__':
    status, b = get('http://nynct.gxzf.gov.cn/')
    html = b.decode('utf-8', errors='replace')
    io.open('_tmp_gx_home.html', 'w', encoding='utf-8').write(html)
    print('status', status, 'len', len(html))
    links = re.findall(r'href="([^"]+)"[^>]*>\s*([^<]{2,40}?)\s*<', html)
    seen = set()
    for h, t in links:
        t = t.strip()
        if any(k in t for k in ['通知', '公告', '公示', '文件', '公开', '检索', '名单', '试点', '示范', '政策']):
            if (t, h) in seen:
                continue
            seen.add((t, h))
            print(t, '->', h)
