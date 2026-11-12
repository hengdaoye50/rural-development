import urllib.request, urllib.parse, ssl, json
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*'}
U = 'http://www.gxzf.gov.cn/jsearchfront/interfaces/search.do'

def post(data):
    body = urllib.parse.urlencode(data).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(U, data=body, headers=UA), timeout=30)
        return json.loads(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        return {'error': str(e)[:80]}

best = None
for sid in range(1, 21):
    for tpl in ['11', '38', '1', '2', '6']:
        r = post({'websiteid': '450000000000000', 'q': '田园综合体', 'p': '1', 'pg': '10',
                  'searchid': str(sid), 'tpl': tpl})
        n = len(r.get('dataResults') or [])
        tot = r.get('total')
        if n and tot:
            d = (r['dataResults'][0].get('similarly') or [{}])[0].get('data') or {}
            print('sid', sid, 'tpl', tpl, 'total', tot, 'n', n, '|', str(d.get('title_str') or d.get('title'))[:50], '|', (d.get('url') or '')[:70])
