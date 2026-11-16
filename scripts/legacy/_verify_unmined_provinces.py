"""验证「政策里提到的片区没被建成 area」：对政策密度高但片区少的省抽样核查。

判据：政策/片区 比值高的省（甘肃 3.1、黑龙江 3.0、内蒙古 3.0、西藏 3.0 等），
若其政策正文里点名了库里没有的片区，就说明片区层欠采、政策富矿未回采。
"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」" + '""' + r"''【】\[\]、，,。.：:；;·—\-－]+")
NAME = re.compile(
    r"[\u4e00-\u9fa5]{2,14}(?:片区组团|田园综合体|示范片区|样板片区|重点片区|"
    r"精品片区|片区|示范带|样板带|先导区|示范片)"
)
GENERIC = ("片区组团", "田园综合体", "乡村振兴示范片区", "乡村振兴示范带", "和美乡村片区",
           "乡村振兴片区", "示范片区", "样板片区", "重点片区", "精品片区",
           "示范带", "样板带", "先导区", "示范片", "片区")
URBAN = ("控规", "详细规划", "地块", "街区", "社区", "开发区", "工业园", "产业园",
         "市场", "广场", "交警", "医院", "学校", "站前", "老城", "棚户", "征收")
RURAL = ("乡村", "振兴", "和美", "示范", "田园", "农", "村")


def norm(s):
    return PUNCT.sub("", s or "")


CASES = [("620000", "甘肃"), ("230000", "黑龙江"), ("150000", "内蒙古"),
         ("540000", "西藏"), ("140000", "山西"), ("650000", "新疆")]

for prov, name in CASES:
    areas = {norm(r["name"]) for r in conn.execute(
        "SELECT name FROM area WHERE province_code=? AND record_state='active'", (prov,))}
    found = set()
    for p in conn.execute(
            "SELECT policy_id, local_path FROM policy WHERE province_code=?", (prov,)):
        body = ROOT / p["local_path"]
        if not body.exists():
            continue
        text = body.read_text(encoding="utf-8")
        for m in NAME.finditer(text):
            cand = m.group(0)
            nc = norm(cand)
            stripped = nc
            for g in GENERIC:
                stripped = stripped.replace(norm(g), "")
            if len(stripped) < 3:
                continue
            if any(u in cand for u in URBAN):
                continue
            ctx = text[max(0, m.start() - 50): m.end() + 50]
            if not any(k in ctx for k in RURAL):
                continue
            if any(nc in a or a in nc for a in areas):
                continue
            found.add(cand)
    print(f"{name}｜库内片区 {len(areas)}｜政策里点名但库里没有的片区候选 {len(found)}")
    for c in sorted(found)[:8]:
        print(f"    {c}")
    print()
