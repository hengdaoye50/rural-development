"""导出实验样本县的现有片区名，作为「是否新增」的判定基准。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

COUNTIES = ["430112", "430423", "430621", "430722", "430723",
            "430781", "430903", "430681", "430702", "430724"]

name = {r["region_code"]: r["name"]
        for r in conn.execute("SELECT region_code, name FROM region WHERE length(region_code)=6")}

for c in COUNTIES:
    rows = conn.execute(
        "SELECT area_id, name FROM area WHERE county_code=? AND record_state='active'", (c,)
    ).fetchall()
    print(f"{c} {name.get(c,'?')}")
    for r in rows:
        print(f"    {r['area_id']} {r['name']}")
