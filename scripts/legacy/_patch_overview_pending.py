"""把 report_corpus_overview.py 的片区统计口径统一为排除 status=待核。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "scripts" / "report_corpus_overview.py"
s = p.read_text(encoding="utf-8")

NA = "record_state='active'"
NA_PENDING = "record_state='active' AND status != '待核'"
NA_A = "a.record_state='active'"
NA_A_PENDING = "a.record_state='active' AND a.status != '待核'"

before = s.count(NA) + s.count(NA_A)
s = s.replace(NA_A, NA_A_PENDING)
s = s.replace(NA, NA_PENDING)
p.write_text(s, encoding="utf-8")
print(f"替换前 {before} 处；写回 {p.relative_to(ROOT)}")
print("含待核排除的行数：", s.count("status != '待核'"))
