import sqlite3, json
c = sqlite3.connect('data/db/片区库.sqlite3')
c.row_factory = sqlite3.Row
sids = ['S320011','S320024','S320004','S510004','S510007','S510008','S510009','S320031','S320064']
q = ','.join('?'*len(sids))
cols = [r[1] for r in c.execute('PRAGMA table_info(source)')]
print('source cols:', cols)
for r in c.execute('select * from source where source_id in (%s)' % q, sids):
    d = dict(r)
    print('=====', d.get('source_id'))
    for k in ('title','url','publisher','publish_ymd','source_kind','credibility','excerpt','area_id'):
        if k in d: print('  %s: %s' % (k, (str(d[k])[:600])))
