"""修复 report_corpus_overview.py 里被批量替换弄出的重复条件。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "scripts" / "report_corpus_overview.py"
s = p.read_text(encoding="utf-8")

bad = "AND status != '待核' AND a.status != '待核'"
good = "AND a.status != '待核'"
n = s.count(bad)
s = s.replace(bad, good)
p.write_text(s, encoding="utf-8")
print(f"修复重复条件 {n} 处")
print("剩余 status != '待核' 出现：", s.count("status != '待核'"))
