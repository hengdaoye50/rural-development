import re, urllib.request, urllib.parse, ssl
ssl._create_default_https_context = ssl._create_unverified_context
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Accept-Language': 'zh-CN,zh;q=0.9'}

kw = urllib.parse.quote('田园综合体')
for sid in range(1, 16):
    for tpl in ['11', '38', '1']:
        u = ('http://zwfw.gxzf.gov.cn/jsearchfront/search.do?websiteid=450000000000000'
             '&searchid=%d&p=1&pg=20&tpl=%s&q=%s' % (sid, tpl, kw))
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25)
            html = r.read().decode('utf-8', errors='replace')
        except Exception as e:
            continue
        hits = re.findall(r'href="(https?://[^"]*gxzf\.gov\.cn[^"]*)"', html)
        ttl = re.search(r'<title>(.*?)</title>', html, re.S)
        if '田园综合体' in html and len(hits) > 0:
            print('searchid', sid, 'tpl', tpl, 'len', len(html), 'title', (ttl.group(1).strip()[:40] if ttl else '?'))
            for h in hits[:5]:
                print('    ', h[:110])
