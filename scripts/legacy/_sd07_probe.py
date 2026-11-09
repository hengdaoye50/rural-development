import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
c = sqlite3.connect('data/db/片区库.sqlite3')
codes = ('370702','370703','370725','370783','370828','370831','370832','370883')
ph = ",".join("?"*len(codes))
q = "select area_id,name,county_code,type_code,status,founded_ymd,issuer,summary from area where county_code in (%s)" % ph
for r in c.execute(q, codes):
    print(r)
print('--- sources ---')
q2 = ("select source_id,area_id,title,url,publisher,published_ymd from source where area_id in "
      "(select area_id from area where county_code in (%s))" % ph)
n = 0
for r in c.execute(q2, codes):
    n += 1
    print(r)
print('n=', n)
