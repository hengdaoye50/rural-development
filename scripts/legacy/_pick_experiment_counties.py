"""为县骨干实验选样本：挑片区数少、且当前有政策全文的县，看县级文件能否挖出新片区名。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

# 候选省：覆盖率中等、县数适中
for prov, name in (("430000", "湖南"), ("340000", "安徽"), ("360000", "江西")):
    rows = conn.execute(
        """
        SELECT a.county_code c, r.name nm, COUNT(*) n,
               SUM(CASE WHEN m.area_id IS NOT NULL THEN 1 ELSE 0 END) cov,
               (SELECT COUNT(*) FROM policy p WHERE p.county_code = a.county_code) np
        FROM area a
        LEFT JOIN (SELECT DISTINCT area_id FROM area_policy_map) m ON m.area_id = a.area_id
        LEFT JOIN region r ON r.region_code = a.county_code
        WHERE a.province_code = ? AND a.record_state='active'
        GROUP BY a.county_code ORDER BY n, a.county_code
        """,
        (prov,),
    ).fetchall()
    print(f"=== {name}（{len(rows)} 县有片区）===")
    for r in rows[:14]:
        print(f"  {r['c']} {r['nm'] or '?':<10} 片区{r['n']} 有依据{r['cov']} "
              f"库内该县政策{r['np']} 份")
    print()
