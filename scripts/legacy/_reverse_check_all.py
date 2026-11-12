"""逆向校验（汇总）：拿库内已有的省级名单，逐省算「名单点名但库内无片区」的县。"""
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row
region = {
    x["region_code"]: x["name"]
    for x in conn.execute("SELECT region_code, name FROM region WHERE length(region_code)=6")
}


def canon(s: str) -> str:
    s = re.sub(r"[（(].*?[)）]", "", s or "")
    for kw in ("满族蒙古族自治县", "满族自治县", "自治县", "县", "市", "区", "新区"):
        s = s.replace(kw, "")
    return s.strip()


def db_units(prov: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in conn.execute(
        "SELECT a.county_code c, a.name n FROM area a "
        "WHERE a.province_code=? AND a.record_state='active'",
        (prov,),
    ):
        key = canon(region.get(r["c"], ""))
        out.setdefault(key, []).append(r["n"])
    return out


# 名单条目：以「数字.」开头，取到第一个行政单元名
ENTRY = re.compile(
    r"(\d+)[.、]\s*([^\n。，,：:]{2,40}?(?:满族蒙古族自治县|满族自治县|自治县|新区|区|县|市))"
)


def roster_units(text: str) -> list[tuple[str, str]]:
    text = re.sub(r"<!--.*?-->", "", text)
    return [(m.group(2), m.group(0)[:60]) for m in ENTRY.finditer(text)]


CASES = [
    ("210000", "辽宁", "data/raw/LN/20230426-ln-sheng-nongwei-2023-shifandai-mingdan/原文.md",
     "2023 省级示范带创建名单 23 条"),
    ("130000", "河北", "data/raw/HE/20250221-he-sheng-2025-pianqu-jingzhengxing-linxuan-tongzhi/原文.md",
     "省级和美乡村重点片区名单（附件1 11 条 + 附件2 11 条）"),
    ("410000", "河南", "data/raw/HA/20260707-ha-sheng-2026-hemei-xiangcun-xianndaoyu-mingdan/原文.md",
     "2026 宜居宜业和美乡村先导区名单"),
    ("420000", "湖北", "data/raw/HB/20261107-hb-sheng-shoupi-20tiao-yangbandai-mingdan/原文.md",
     "首批 20 条和美乡村样板带"),
]

for prov, name, rel, desc in CASES:
    p = ROOT / rel
    print("=" * 72)
    print(f"{name}｜{desc}")
    if not p.exists():
        print("  原文缺失，跳过")
        continue
    units = roster_units(p.read_text(encoding="utf-8"))
    db = db_units(prov)
    db_keys = set(db)
    miss = [(u, raw) for u, raw in units if canon(u) not in db_keys]
    print(f"  名单解析出 {len(units)} 条，涉及 {len({canon(u) for u, _ in units})} 个县（区）")
    print(f"  库内 {name} 有片区的县 {len(db_keys)} 个：{'、'.join(sorted(db_keys))}")
    print(f"  名单点名但库内该县无片区：{len({canon(u) for u, _ in miss})} 个县")
    seen = set()
    for u, raw in miss:
        k = canon(u)
        if k in seen:
            continue
        seen.add(k)
        print(f"    - {raw}")
