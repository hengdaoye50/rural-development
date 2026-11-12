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

for kw in ['百李挑一', '嘹啰歌乡', '田园综合体试点项目']:
    r = post({'websiteid': '450000000000000', 'fullq': kw, 'p': '1', 'pg': '20'})
    print('==', kw, 'total', r.get('total'))
    for it in (r.get('dataResults') or [])[:8]:
        d = (it.get('similarly') or [{}])[0].get('data') or {}
        print('   ', d.get('title_str') or d.get('title'), '|', d.get('typename'), '|', (d.get('url') or '')[:90], '|', d.get('cd_time'))
