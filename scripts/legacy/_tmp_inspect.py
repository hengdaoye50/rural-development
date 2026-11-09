import sqlite3

c = sqlite3.connect('data/db/片区库.sqlite3')
cur = c.cursor()
print('TABLES:', [r[0] for r in cur.execute("select name from sqlite_master where type='table'")])
print('--- area cols')
for r in cur.execute('PRAGMA table_info(area)'):
    print(r)
ids = ['A440029', 'A440028', 'A440032', 'A440031', 'A440034', 'A440011',
       'A440012', 'A440013', 'A440014', 'A440015', 'A440016', 'A440036']
q = 'select area_id,name,county_code,type_code,status,first_source_id from area where area_id in (%s)' % ','.join('?' * len(ids))
print('--- rows')
for r in cur.execute(q, ids):
    print(r)
print('--- policy cols')
for r in cur.execute('PRAGMA table_info(policy)'):
    print(r)
