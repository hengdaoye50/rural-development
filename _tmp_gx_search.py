import urllib.request, ssl, urllib.parse, json, sys
ssl._create_default_https_context = ssl._create_unverified_context

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Accept': '*/*', 'Accept-Language': 'zh-CN,zh;q=0.9'}

def try_url(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30)
        b = r.read()
        return r.status, b
    except Exception as e:
        return None, str(e)[:160].encode('utf-8', 'replace')

q = urllib.parse.quote('田园综合体')
cands = [
    'http://www.gxzf.gov.cn/jsearchfront/interfaces/search.do?websiteid=450000000000000&q=%s&p=1&pg=10' % q,
    'http://www.gxzf.gov.cn/jsearchfront/search.do?websiteid=450000000000000&q=%s&p=1&pg=10' % q,
    'https://zwfw.gxzf.gov.cn/jsearchfront/interfaces/search.do?websiteid=450000000000000&q=%s&p=1&pg=10' % q,
    'http://www.gxzf.gov.cn/jsearchfront/interfaces/wordranklist.do',
]
for u in cands:
    s, b = try_url(u)
    print('==', u)
    print('   status', s, 'len', len(b))
    print('   head:', b[:400].decode('utf-8', errors='replace').replace('\n', ' '))
