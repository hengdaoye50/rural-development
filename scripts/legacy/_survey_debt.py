"""Survey quality debt: unknown time / 待核 / unknown scale."""
import sqlite3

DB = r"D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3"
c = sqlite3.connect(DB)

print("=== time unknown by province ===")
for r in c.execute(
    "select province_code,count(*) n from area "
    "where founded_precision='unknown' or founded_precision is null or founded_precision='' "
    "group by province_code order by n desc limit 15"
):
    print(r)

print("\n=== 待核 by province ===")
for r in c.execute(
    "select province_code,count(*) n from area where status='待核' group by province_code order by n desc limit 15"
):
    print(r)

print("\n=== scale unknown ===")
print(
    list(
        c.execute(
            "select count(*) from area where (scale_villages is null or scale_villages='') "
            "and (scale_towns is null or scale_towns='')"
        )
    )
)

print("\n=== sample unknown-time rows ===")
for r in c.execute(
    "select area_id,name,province_code,founded_ymd,founded_precision,substr(coalesce(summary,''),1,80) "
    "from area where founded_precision='unknown' or founded_precision is null limit 8"
):
    print(r)

print("\n=== sample 待核 rows ===")
for r in c.execute(
    "select area_id,name,province_code,status,substr(coalesce(type_primary_note,''),1,80) "
    "from area where status='待核' limit 8"
):
    print(r)

print("\n=== founded_ymd empty but precision not unknown ===")
print(
    list(
        c.execute(
            "select count(*) from area where (founded_ymd is null or founded_ymd='') "
            "and founded_precision!='unknown'"
        )
    )
)

print("\n=== precision distribution ===")
for r in c.execute(
    "select founded_precision,count(*) from area group by founded_precision order by 2 desc"
):
    print(r)
