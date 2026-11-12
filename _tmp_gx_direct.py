import re, io, sys
from _tmp_gx_probe import get

urls = [
    'https://4g.bgxf.gov.cn/staticpages/20220628/newgx62ba541a-117478.shtml',
    'http://www.gxhczx.gov.cn/news_view.php?id=49211',
    'http://www.gxzx.gov.cn/index.php?m=content&c=index&a=show&catid=69&id=46131',
]
for i, u in enumerate(urls):
    try:
        s, b = get(u, timeout=35)
    except Exception as e:
        print(u, 'ERR', type(e).__name__, str(e)[:90]); continue
    html = b.decode('utf-8', errors='replace')
    io.open('_tmp_page%d.html' % i, 'w', encoding='utf-8').write(html)
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text).strip()
    print('==', u, s, len(html))
    for kw in ['田园综合体']:
        for m in re.finditer(kw, text):
            seg = text[max(0, m.start() - 200):m.start() + 300].replace('\n', ' ')
            print('   ...', seg[:400])
            break
