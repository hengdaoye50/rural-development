"""Ad-hoc stats for XZ verify + JS/ZJ/SD comparison."""
import sqlite3

DB = r"D:\CODEX\全国乡村片区化数据库\data\db\片区库.sqlite3"
c = sqlite3.connect(DB)

print("=== XZ ===")
for r in c.execute(
    "select area_id,name,type_code,status,founded_precision from area where province_code='540000'"
):
    print(r)
print("belt", list(c.execute("select belt_id,name from belt where province_code='540000'")))
print("src", list(c.execute("select source_id,title from source where source_id like 'S54%'")))
print("provs", list(c.execute("select count(distinct province_code) from area")))

print("\n=== JS/ZJ/SD type mix ===")
for pc, name in [("320000", "江苏"), ("330000", "浙江"), ("370000", "山东")]:
    print(name)
    for r in c.execute(
        "select type_code,count(*) from area where province_code=? group by type_code order by 2 desc",
        (pc,),
    ):
        print(" ", r)
    print(
        "  status",
        list(c.execute("select status,count(*) from area where province_code=? group by status", (pc,))),
    )
    print(
        "  top tags",
        list(
            c.execute(
                "select tags,count(*) from area where province_code=? and tags!='' group by tags order by 2 desc limit 5",
                (pc,),
            )
        ),
    )
    print(
        "  parent",
        list(
            c.execute(
                "select parent_area_key,count(*) from area where province_code=? and parent_area_key!='' group by parent_area_key order by 2 desc limit 6",
                (pc,),
            )
        ),
    )

print("\n=== national type x status ===")
for r in c.execute("select type_code,status,count(*) from area group by type_code,status order by 1,3 desc"):
    print(r)

print("\n=== counties covered ===")
print("area counties", list(c.execute("select count(distinct county_code) from area where county_code!=''")))
print(
    "top provinces by area",
    list(
        c.execute(
            "select province_code,count(*) n from area group by province_code order by n desc limit 8"
        )
    ),
)
print(
    "T02 by province",
    list(
        c.execute(
            "select province_code,count(*) n from area where type_code='T02' group by province_code order by n desc limit 8"
        )
    ),
)
print(
    "belt by type",
    list(c.execute("select belt_type,count(*) from belt group by belt_type order by 2 desc")),
)
