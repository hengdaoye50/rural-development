import sqlite3

c = sqlite3.connect('data/db/片区库.sqlite3')
cur = c.cursor()
for s in ['S440003', 'S440004', 'S440008', 'S440009', 'S440010']:
    q = "select source_id,title,url,publisher,published_ymd from source where source_id=?"
    for r in cur.execute(q, (s,)):
        print(r)
    print()
