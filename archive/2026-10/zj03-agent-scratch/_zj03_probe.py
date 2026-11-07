import sqlite3, sys, io
sys.stdout.reconfigure(encoding="utf-8")
con = sqlite3.connect(r"D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3")
cur = con.cursor()
cur.execute("select name from sqlite_master where type='table'")
print("TABLES:", [r[0] for r in cur.fetchall()])
for t in ("source", "policy"):
    try:
        cur.execute(f"PRAGMA table_info({t})")
        print(t, "COLS:", [r[1] for r in cur.fetchall()])
    except Exception as e:
        print(t, e)
