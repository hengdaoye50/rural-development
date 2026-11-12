import urllib.request, urllib.parse, ssl, json
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*'}
U = 'http://www.gxzf.gov.cn/jsearchfront/interfaces/search.do'

def post(data):
    body = urllib.parse.urlencode(data).encode()
    try:
        r = urllib.request.urlopen(urllib.request.Request(U, data=body, headers=UA), timeout=40)
        return json.loads(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        return {'err': str(e)[:160]}

q = '田园综合体'
combos = [
    {'websiteid': '450000000000000', 'q': q, 'p': '1', 'pg': '10', 'searchid': '2', 'tpl': '11', 'cateid': '18'},
    {'websiteid': '450000000000000', 'word': q, 'q': q, 'p': '1', 'pg': '10', 'searchid': '2', 'tpl': '11'},
    {'websiteid': '450000000000000', 'fullq': q, 'p': '1', 'pg': '10'},
    {'websiteid': '450000000000000', 'q': q, 'p': '1', 'pg': '10', 'pos': 'title'},
    {'websiteid': '450000000000000', 'q': q, 'p': '1', 'pg': '10', 'tpl': ''},
    {'websiteid': '450000000000000', 'q': '乡村振兴', 'p': '1', 'pg': '10'},
]
for c in combos:
    r = post(c)
    print('--', {k: v for k, v in c.items() if k in ('q', 'word', 'fullq', 'searchid', 'tpl', 'cateid', 'pos')})
    print('   total', r.get('total'), 'hits', r.get('totalHits'), 'n', len(r.get('dataResults') or []), 'err', r.get('err'))
    dr = r.get('dataResults') or []
    if dr:
        print('   keys', list(dr[0].keys())[:25])
        for it in dr[:3]:
            print('   ', str(it.get('title'))[:70], '|', str(it.get('url'))[:80])
