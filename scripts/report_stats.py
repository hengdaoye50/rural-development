"""常用统计查询（验收/报告用）。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "db" / "片区库.sqlite3"

QUERIES = {
    "总量": """
        select 'area' t, count(*) n from area
        union all select 'belt', count(*) from belt
        union all select 'source', count(*) from source
    """,
    "分省": """
        select province_code, count(*) n,
               count(distinct city_code) cities,
               count(distinct county_code) counties
        from area group by province_code
    """,
    "类型": "select type_code, count(*) from area group by type_code order by type_code",
    "状态": "select status, count(*) from area group by status",
    "时间精度": "select founded_precision, count(*) from area group by founded_precision",
    "来源等级": "select credibility, count(*) from source group by credibility",
    "带类型": "select belt_type, count(*) from belt group by belt_type",
    "片区规模": """
        select case
            when scale_villages is null or scale_villages='' then 'unknown'
            when cast(scale_villages as integer)<5 then '1-4'
            when cast(scale_villages as integer)<10 then '5-9'
            when cast(scale_villages as integer)<20 then '10-19'
            else '20+' end bucket, count(*)
        from area group by bucket
    """,
    "代表片区": """
        select province_code, name, type_code, county_code, founded_ymd, status
        from area where record_state='active'
        order by province_code, type_code, name limit 30
    """,
}


def main() -> None:
    conn = sqlite3.connect(DB)
    for title, sql in QUERIES.items():
        print(f"\n=== {title} ===")
        for row in conn.execute(sql):
            print(row)
    conn.close()


if __name__ == "__main__":
    main()
