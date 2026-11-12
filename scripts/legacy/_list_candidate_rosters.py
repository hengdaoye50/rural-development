"""反查第一步：列出库内「名单/公布/批复」类的省级政策，作为逆向校验的起点。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

PROV = {
    "110000": "北京", "120000": "天津", "130000": "河北", "140000": "山西",
    "150000": "内蒙古", "210000": "辽宁", "220000": "吉林", "230000": "黑龙江",
    "310000": "上海", "320000": "江苏", "330000": "浙江", "340000": "安徽",
    "350000": "福建", "360000": "江西", "370000": "山东", "410000": "河南",
    "420000": "湖北", "430000": "湖南", "440000": "广东", "450000": "广西",
    "460000": "海南", "500000": "重庆", "510000": "四川", "520000": "贵州",
    "530000": "云南", "540000": "西藏", "610000": "陕西", "620000": "甘肃",
    "630000": "青海", "640000": "宁夏", "650000": "新疆",
}

rows = conn.execute(
    """
    SELECT policy_id, province_code, issuer_level, title, local_path, full_text_chars,
           target_areas
    FROM policy
    WHERE (title LIKE '%名单%' OR title LIKE '%公布%' OR title LIKE '%批复%'
           OR title LIKE '%认定%' OR title LIKE '%示范片区%')
      AND issuer_level IN ('province', 'city')
    ORDER BY province_code, policy_id
    """
).fetchall()

cur = None
for r in rows:
    if r["province_code"] != cur:
        cur = r["province_code"]
        n_area = conn.execute(
            "SELECT COUNT(*) FROM area WHERE province_code=? AND record_state='active'",
            (cur,),
        ).fetchone()[0]
        print(f"\n===== {PROV.get(cur, cur)}（库内片区 {n_area}）=====")
    ta = f"  target_areas={r['target_areas']}" if r["target_areas"] else ""
    print(f"  {r['policy_id']} [{r['issuer_level']}] {r['title'][:56]}")
    print(f"      {r['full_text_chars']} 字{ta}  {r['local_path']}")
