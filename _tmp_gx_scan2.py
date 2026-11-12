import re, io, time
from _tmp_gx_probe import get

COLS = {
    'czt_tzgg': 'http://czt.gxzf.gov.cn/xwdt/tzgg/',
    'czt_zcwj': 'http://czt.gxzf.gov.cn/zfxxgkzl/zcwj/',
    'nynct_jyta': 'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/jytajggk/',
}
KEY = re.compile(r'田园综合体|片区|示范带|组团|乡村振兴示范|和美乡村')
out = []
for name, base in COLS.items():
    for p in range(26):
        u = base + ('index.shtml' if p == 0 else 'index_%d.shtml' % p)
        try:
            s, b = get(u, timeout=25)
        except Exception as e:
            print(name, p, 'ERR', str(e)[:60]); break
        html = b.decode('utf-8', errors='replace')
        items = re.findall(r'<a[^>]+href="([^"]*t\d+\.shtml)"[^>]*>\s*([^<]{4,120}?)\s*</a>', html)
        for h, t in items:
            out.append((name, p, t.strip(), h))
        if not items:
            print(name, p, 'empty -> stop'); break
        time.sleep(0.15)

io.open('_tmp_gx_czt_titles.tsv', 'w', encoding='utf-8').write(
    '\n'.join('\t'.join(map(str, r)) for r in out))
print('titles', len(out))
print('--- keyword hits ---')
for r in out:
    if KEY.search(r[2]):
        print(r[0], '|', r[2], '|', r[3])
