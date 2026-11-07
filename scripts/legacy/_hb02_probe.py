import sqlite3, json
c = sqlite3.connect('data/db/片区库.sqlite3')
c.row_factory = sqlite3.Row
ids = ('A420018','A420017','A420007','A420019','A420014','A420013','A420020','A420009')
q = "select * from area where area_id in (%s)" % ",".join("?"*len(ids))
for r in c.execute(q, ids):
    d = dict(r)
    print(json.dumps({k: v for k, v in d.items() if k in ('area_id','area_name','province','city','county','town','type_code','first_source_id','status','established_ymd','description','village_count','area_scope')}, ensure_ascii=False))
print('--- sources ---')
q2 = "select * from source where area_id in (%s) or source_id in (select first_source_id from area where area_id in (%s))" % (",".join("?"*len(ids)), ",".join("?"*len(ids)))
for r in c.execute(q2, ids+ids):
    d = dict(r)
    print(json.dumps({k: v for k, v in d.items() if k in ('source_id','area_id','title','url','publisher','published_ymd','local_path')}, ensure_ascii=False))
