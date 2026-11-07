import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3")
cur = con.cursor()
codes = ["330203", "330206", "330212", "330324", "330326", "330327", "330328", "330329"]
print("=== areas for ZJ03 counties ===")
for c in codes:
    cur.execute("""select area_id, name, founded_ymd, issuer, first_source_id, summary
                   from area where county_code=?""", (c,))
    rows = cur.fetchall()
    print("---", c, len(rows))
    for r in rows:
        print("   ", r[0], "|", r[1], "|", r[2], "|", r[3], "|", r[4])
        if r[5]:
            print("      summary:", (r[5] or "")[:200])
print()
print("=== sources linked to these counties' areas ===")
for c in codes:
    cur.execute("""select s.source_id, s.area_id, s.url, s.title, s.published_ymd, s.publisher
                   from source s join area a on a.area_id = s.area_id
                   where a.county_code=?""", (c,))
    for r in cur.fetchall():
        print(c, "|", r[0], "|", r[2], "|", r[3], "|", r[5])
print()
print("=== existing policy rows for these counties ===")
for c in codes:
    cur.execute("select policy_id,title,url from policy where county_code=?", (c,))
    for r in cur.fetchall():
        print(c, "|", r)
cur.execute("select count(*) from policy")
print("policy total:", cur.fetchone())
