import urllib.request, urllib.parse, ssl, json
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'}

def get(u, timeout=40):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout)
    return r.read()

tgt = 'www.gxny.gov.cn/xxgk/jcxxgk/tzgg_43/t622364.html'
for u in ['http://archive.org/wayback/available?url=' + urllib.parse.quote(tgt),
          'http://web.archive.org/cdx/search/cdx?url=' + urllib.parse.quote(tgt) + '&output=json&limit=20']:
    print('==', u)
    try:
        print(get(u).decode('utf-8', errors='replace')[:1200])
    except Exception as e:
        print('ERR', type(e).__name__, str(e)[:120])
    print()

# CDX for any gxny page containing tianyuanzhongheti notices
u = 'http://web.archive.org/cdx/search/cdx?url=gxny.gov.cn*&output=json&limit=50&filter=urlkey:.*tianyuan.*'
try:
    print(get(u).decode('utf-8', errors='replace')[:1500])
except Exception as e:
    print('cdx wildcard ERR', type(e).__name__, str(e)[:120])
