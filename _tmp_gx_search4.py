import urllib.request, urllib.parse, ssl, json
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*'}
U = 'http://www.gxzf.gov.cn/jsearchfront/interfaces/search.do'

def post(data):
    body = urllib.parse.urlencode(data).encode()
    r = urllib.request.urlopen(urllib.request.Request(U, data=body, headers=UA), timeout=40)
    return json.loads(r.read().decode('utf-8', errors='replace'))

r = post({'websiteid': '450000000000000', 'fullq': '田园综合体 试点项目 名单', 'p': '1', 'pg': '20'})
print('total', r.get('total'))
for it in (r.get('dataResults') or [])[:2]:
    print(json.dumps(it, ensure_ascii=False)[:2500])
    print('-----')
