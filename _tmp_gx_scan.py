import re, io, time
from _tmp_gx_probe import get

COLUMNS = {
    'tzgg': 'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/tzgg/',
    'gntgg': 'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntgg/',
    'gntf': 'http://nynct.gxzf.gov.cn/xxgk/jcxxgk/wjzl/gntf/',
}
KEY = re.compile(r'名单|公示|示范|片区|田园综合体|试点|公布|认定|批准')
out = []
for name, base in COLUMNS.items():
    for p in range(25):
        u = base + ('index.shtml' if p == 0 else 'index_%d.shtml' % p)
        try:
            s, b = get(u, timeout=25)
        except Exception as e:
            print(name, p, 'ERR', str(e)[:60])
            break
        html = b.decode('utf-8', errors='replace')
        found = 0
        for h, t in re.findall(r'<a[^>]+href="([^"]*t\d+\.shtml)"[^>]*>\s*([^<]{6,120}?)\s*</a>', html):
            found += 1
            out.append((name, p, t.strip(), h))
        if found == 0:
            print(name, p, 'no items, stop')
            break
        time.sleep(0.2)
io.open('_tmp_gx_all_titles.tsv', 'w', encoding='utf-8').write(
    '\n'.join('\t'.join(map(str, r)) for r in out))
print('total titles', len(out))
hits = [r for r in out if KEY.search(r[2])]
print('keyword hits', len(hits))
for r in hits:
    print(r[0], '|', r[2], '|', r[3])
