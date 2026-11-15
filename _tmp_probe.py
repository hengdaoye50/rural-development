import sqlite3, sys
c = sqlite3.connect('data/db/片区库.sqlite3')
c.row_factory = sqlite3.Row
ids = ['A510007','A510008','A510009','A510016','A510017','A510018','A320012','A320013','A320014','A320029','A320036']
cols = [r[1] for r in c.execute('PRAGMA table_info(area)')]
print('area cols:', cols)
q = ','.join('?'*len(ids))
sel = [x for x in ['area_id','name','area_name','county_code','county_name','level','type_code','status','status_note','definition','first_source_id'] if x in cols]
sql = 'select %s from area where area_id in (%s)' % (','.join(sel), q)
for r in c.execute(sql, ids):
    print(dict(r))
print('--- policy linked')
for r in c.execute('select area_id, count(*) from area_policy_map where area_id in (%s) group by area_id' % q, ids):
    print(tuple(r))
print('--- sources linked')
for r in c.execute('select area_id, source_id, rel from area_source_map where area_id in (%s)' % q, ids):
    print(tuple(r))
