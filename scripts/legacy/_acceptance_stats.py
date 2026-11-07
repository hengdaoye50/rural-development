import sqlite3
from pathlib import Path

db = Path("data/db/片区库.sqlite3")
conn = sqlite3.connect(db)
cur = conn.cursor()

def q(sql):
    return cur.execute(sql).fetchall()

print("=== 表规模 ===")
for t in ["area", "belt", "source", "region", "area_region_map", "belt_region_map"]:
    print(t, q(f"select count(*) from {t}")[0][0])

print("\n=== area 按省 ===")
for r in q("""
select province_code, count(*) n,
  sum(case when status='运行中' then 1 else 0 end) running,
  sum(case when status='待核' then 1 else 0 end) pending
from area group by province_code order by province_code
"""):
    print(r)

print("\n=== area 类型 ===")
for r in q("select type_code, count(*) from area group by type_code order by type_code"):
    print(r)

print("\n=== belt 类型 ===")
for r in q("select belt_type, count(*) from belt group by belt_type"):
    print(r)

print("\n=== 覆盖地级市数 ===")
for r in q("select province_code, count(distinct city_code) from area group by province_code"):
    print(r)

print("\n=== 覆盖县数 ===")
for r in q("select province_code, count(distinct county_code) from area group by province_code"):
    print(r)

print("\n=== 来源等级 ===")
for r in q("select credibility, count(*) from source group by credibility order by credibility"):
    print(r)

print("\n=== 时间精度 ===")
for r in q("select founded_precision, count(*) from area group by founded_precision"):
    print(r)

print("\n=== 有村数的片区规模分布 ===")
for r in q("""
select case
  when scale_villages is null or scale_villages='' then 'unknown'
  when cast(scale_villages as integer) < 5 then '1-4'
  when cast(scale_villages as integer) < 10 then '5-9'
  when cast(scale_villages as integer) < 20 then '10-19'
  else '20+' end bucket, count(*)
from area group by bucket
"""):
    print(r)

print("\n=== 样本（每省3条） ===")
for prov in ["320000", "330000", "370000"]:
    rows = q(f"""
    select name, type_code, county_code, cover_desc, status
    from area where province_code='{prov}' and record_state='active'
    limit 3
    """)
    print(prov)
    for r in rows:
        print(" ", r)

conn.close()
