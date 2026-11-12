import urllib.request, urllib.parse, ssl, json
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*'}

def post(u, data):
    body = urllib.parse.urlencode(data).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, data=body, headers=UA), timeout=40)
        return r.status, r.read()
    except Exception as e:
        return None, str(e)[:200].encode('utf-8', 'replace')

bases = ['http://www.gxzf.gov.cn/jsearchfront/interfaces/search.do',
         'https://zwfw.gxzf.gov.cn/jsearchfront/interfaces/search.do']
data = {'websiteid': '450000000000000', 'q': '田园综合体', 'p': '1', 'pg': '10',
        'cateid': '', 'pos': '', 'tpl': '', 'serviceType': '', 'checkError': '1'}
for u in bases:
    s, b = post(u, data)
    print('==', u, s, len(b))
    txt = b.decode('utf-8', errors='replace')
    print(txt[:1500])
    print()
