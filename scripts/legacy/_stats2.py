import sqlite3

c = sqlite3.connect("data/db/片区库.sqlite3")
print("founded_precision:", c.execute("select founded_precision, count(*) from area group by 1").fetchall())
print("status:", c.execute("select status, count(*) from area group by 1").fetchall())
print("local_path:", c.execute("select case when local_path is null or local_path='' then 0 else 1 end, count(*) from source group by 1").fetchall())
print("map rows:", c.execute("select count(*) from area_source_map").fetchone()[0])
print("area:", c.execute("select count(*) from area").fetchone()[0])
print("belt:", c.execute("select count(*) from belt").fetchone()[0])
print("source:", c.execute("select count(*) from source").fetchone()[0])
