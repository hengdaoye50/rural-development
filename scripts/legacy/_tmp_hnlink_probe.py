import sqlite3, sys

ids = ['A430004','A430005','A430006','A430007','A430009','A430011','A430015',
       'A430017','A430019','A430020','A430021','A430022','A430023','A430024',
       'A430025','A430026']
c = sqlite3.connect('data/db/片区库.sqlite3')
q = 'select area_id,county_code,area_name,type_code,record_state from area where area_id in (%s)' % ','.join('?'*len(ids))
for r in c.execute(q, ids):
    print(r)
print('--- columns ---')
print([d[1] for d in c.execute('PRAGMA table_info(area)')])
print('--- policy cols ---')
print([d[1] for d in c.execute('PRAGMA table_info(policy)')])
