"""逆向校验·辽宁：解析省 2023 年示范带创建名单（23 条），与库内片区对账。

名单原文是 OCR 转录，有断行与错字，故按「行政单元」而非片区别名对账：
名单覆盖哪些县（市、区），库内这些县有没有片区记录。
"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/raw/LN/20230426-ln-sheng-nongwei-2023-shifandai-mingdan/原文.md"

text = SRC.read_text(encoding="utf-8")
# 去掉分页注释与页脚页码
text = re.sub(r"<!--.*?-->", "", text)
text = re.sub(r"\n-\d+-\n", "\n", text)

# 示范带条目：以「数字.」开头、以「乡村振兴示（范带）」结尾
entries = re.findall(r"\d+\.\s*([^\n]{2,90}?)\s*乡村振兴示(?:范带|范\s*\n?\s*带)?", text)
print(f"解析到示范带条目 {len(entries)} 条\n")

# 取条目前半段的第一个行政单元名（如「沈北新区」「庄河市」「桓仁满族自治县」）
ADMIN = re.compile(
    r"^([\u4e00-\u9fa5]{2,12}?(?:新区|满族自治县|自治县|区|县|市))"
)
units = []
for e in entries:
    e = e.replace("一", "-").replace("—", "-").strip()
    m = ADMIN.match(e)
    if m:
        units.append((m.group(1), e[:60]))
    else:
        units.append(("?", e[:60]))

for u, e in units:
    print(f"  {u:<12}{e}")

covered = {u for u, _ in units if u != "?"}
print(f"\n名单覆盖行政单元 {len(covered)} 个：{'、'.join(sorted(covered))}")

# 库内辽宁片区按县分布
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT county_code, COUNT(*) n, GROUP_CONCAT(name, ' / ') names FROM area "
    "WHERE province_code='210000' AND record_state='active' GROUP BY county_code"
).fetchall()
print(f"\n库内辽宁片区涉及 {len(rows)} 个县（区）：")
for r in rows:
    print(f"  {r['county_code']}  {r['n']} 个：{r['names'][:70]}")

# 用 region 表把县码映射回县名，便于与名单比对
region = {
    x["region_code"]: x["name"]
    for x in conn.execute("SELECT region_code, name FROM region WHERE length(region_code)=6")
}

db_units = set()
for r in rows:
    nm = region.get(r["county_code"], "")
    if nm:
        db_units.add(nm)
print(f"\n库内有片区的县名 {len(db_units)} 个：{'、'.join(sorted(db_units))}")

# 名单写法与 region 名常有差异（县/市/自治县、OCR 错字），做一次宽松匹配
def canon(s: str) -> str:
    return (
        s.replace("满族自治县", "")
        .replace("自治县", "")
        .replace("县", "")
        .replace("市", "")
        .replace("区", "")
    )

db_canon = {canon(x) for x in db_units}
missing = [u for u in sorted(covered) if canon(u) not in db_canon]
print(f"\n名单里出现、但库内该县无任何片区：{len(missing)} 个")
for m in missing:
    print(f"  {m}")
