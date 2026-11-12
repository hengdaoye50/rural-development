"""量化「已入库全文里可挖掘但未结构化的维度」，用于判断补维度的成本。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT policy_id, province_code, local_path, title FROM policy").fetchall()
texts = []
for r in rows:
    p = ROOT / r["local_path"]
    if p.exists():
        texts.append((r["policy_id"], r["province_code"], p.read_text(encoding="utf-8")))

n = len(texts)
print(f"可读全文 {n} 份\n")

PROBES = {
    "含「个行政村」（覆盖面）": r"\d+\s*个行政村",
    "含「个村」（覆盖面）": r"\d+\s*个村",
    "含村名枚举（≥3 个「XX村」并列）": r"(?:[\u4e00-\u9fa5]{2,4}村[、，,]){3}",
    "含「万元」（资金）": r"\d[\d,.]*\s*万元",
    "含「亿元」（资金）": r"\d[\d,.]*\s*亿元",
    "含「考核」（机制）": r"考核",
    "含「评分/分值/得分」": r"(评分|分值|得分)",
    "含「验收」": r"验收",
    "含「排名/名次/等次」": r"(排名|名次|等次)",
    "含「领导小组」成员名单迹象": r"(组长|副组长|成员单位)",
    "含「人口」（底数）": r"\d[\d,.]*\s*(万?人)",
    "含「平方公里/亩」（面积）": r"(平方公里|\d[\d,.]*\s*亩)",
    "含「挂牌/揭牌」（物证）": r"(挂牌|揭牌)",
    "含「撤销/退出/摘牌」": r"(撤销|退出|摘牌)",
}

for label, pat in PROBES.items():
    rx = re.compile(pat)
    hit = sum(1 for _pid, _p, t in texts if rx.search(t))
    print(f"  {label:<34}{hit:>5} 份  ({hit/n*100:.0f}%)")

print("\n=== area 侧：覆盖村名单是否已结构化 ===")
for col in ("scale_villages", "town_codes", "lead_org"):
    c = conn.execute(
        f"SELECT COUNT(*) FROM area WHERE record_state='active' AND {col} IS NOT NULL AND {col} != ''"
    ).fetchone()[0]
    print(f"  {col:<16}{c}/1064")
print("\n（注意：库里没有任何字段存「覆盖哪些行政村」的名单本身）")
