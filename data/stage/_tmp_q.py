import sqlite3, sys
c = sqlite3.connect(r'D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3')
codes = ['430112','430423','430621','430722','430723','430781','430903','430681','430702','430724']
for cd in codes:
    rows = c.execute("select area_id, area_name, type_code, status from area where county_code like ?", (cd + '%',)).fetchall()
    print(cd, len(rows))
    for r in rows:
        print('   ', r)
