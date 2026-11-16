"""人工核验实验抽出的 10 个候选片区名：确认 (a) 原文确有、(b) 库内确无。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

CANDS = [
    ("371321", "东高庄红色片区"),
    ("371321", "双堠水库片区"),
    ("371321", "双峪养生谷片区"),
    ("445103", "凤凰茶谷示范带"),
    ("445103", "梅林湖片区"),
    ("331022", "亭旁红色大道精品片区"),
    ("331022", "健跳美丽田园精品片区"),
    ("441403", "松口镇农文旅融合发展片区"),
    ("430703", "港中坪片区"),
    ("370103", "泉韵乡居和美乡村片区"),
]

all_names = [
    (r["area_id"], r["county_code"], r["name"])
    for r in conn.execute("SELECT area_id, county_code, name FROM area")
]

print("候选名 | 县码 | 原文出处 | 库内同名 | 同县现有片区")
print("=" * 78)
ok_in_src = 0
ok_not_in_db = 0
for cc, name in CANDS:
    src_hit = ""
    for r in conn.execute(
        "SELECT policy_id, local_path FROM policy WHERE county_code=? AND doc_type='报告'",
        (cc,),
    ):
        body = ROOT / r["local_path"]
        if body.exists() and name in body.read_text(encoding="utf-8"):
            src_hit = r["policy_id"]
            break
    same = [a[2] for a in all_names if a[1] == cc and name in a[2]]
    print(f"{name} | {cc} | {src_hit or '未找到'} | {'是' if same else '否'} | "
          f"{'、'.join(s[:14] for s in same[:2]) or '-'}")
    if src_hit:
        ok_in_src += 1
    if not same:
        ok_not_in_db += 1

print()
print(f"原文可核 {ok_in_src}/10；库内无同名 {ok_not_in_db}/10")
