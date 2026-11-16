import sqlite3
c = sqlite3.connect(r'D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3')
cols = [r[1] for r in c.execute('PRAGMA table_info(source)')]
print(cols)
names = ['望城', '衡山', '岳阳', '汉寿', '澧', '津市', '赫山', '汨罗', '武陵', '临澧']
for n in names:
    rows = c.execute("select url, title from source where title like ? or url like ?", ('%' + n + '%', '%' + n + '%')).fetchall()
    seen = []
    for u, t in rows:
        from urllib.parse import urlparse
        try:
            host = urlparse(u).netloc
        except Exception:
            host = '?'
        if host not in seen:
            seen.append(host)
            print(n, host, '|', (t or '')[:40])
    if not seen:
        print(n, 'no source rows')
