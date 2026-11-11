"""生成片区名对照登记表：库内名 ↔ 官方文本中的写法 ↔ 出处政策。

判据与用途：
  - `疑似漂移`：库内名与全文中的近似写法相似度低，很可能是同一片区的另一种叫法
  - `未命名的官方名`：库内名在全文一次都没出现，但同县政策里出现了形近写法

本表**只做登记，不改数据**。改名会改变实体身份，必须逐条确认官方出处后再由
apply_area_fixes.py 执行；同一片区的两套叫法应保留库内名、登记官方别名。

用法：
  python scripts/propose_name_alignment.py
  python scripts/propose_name_alignment.py --csv reports/qa/area-name-registry.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports" / "qa" / "area-name-audit.csv"
DEFAULT_CSV = ROOT / "reports" / "qa" / "area-name-registry.csv"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－−]+")

# 通用词组：出现在官方文本里但**不是片区名**，模糊匹配常把它们当「官方写法」
GENERIC = (
    "乡村振兴片区", "乡村振兴示范片区", "乡村振兴示范带", "乡村振兴示范片",
    "乡村振兴示范区", "乡村振兴建设片", "乡村振兴示范村", "乡村片区",
    "示范片区", "示范带", "示范片", "片区组团", "重点村组团片区",
    "新乡村示范带", "和美乡村片区", "精品片区", "样板片区",
)


def is_generic(form: str) -> bool:
    f = norm(form)
    if not f:
        return True
    # 去掉通用词组后若剩不下 3 个字，说明它本身就是通用词组
    for g in GENERIC:
        f = f.replace(g, "")
    return len(f) < 3


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def main() -> int:
    to_csv = DEFAULT_CSV
    if "--csv" in sys.argv:
        to_csv = Path(sys.argv[sys.argv.index("--csv") + 1])

    if not AUDIT.exists():
        print(f"缺 {AUDIT.relative_to(ROOT)}，先跑 scripts/audit_area_names.py --csv")
        return 1

    conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
    conn.row_factory = sqlite3.Row

    # 按省缓存政策全文，供定位出处
    cache: dict[str, list[tuple[str, str, str]]] = {}
    for p in conn.execute("SELECT policy_id, province_code, local_path FROM policy"):
        body = ROOT / p["local_path"]
        if not body.exists():
            continue
        cache.setdefault(p["province_code"], []).append(
            (p["policy_id"], p["local_path"], norm(body.read_text(encoding="utf-8")))
        )

    area_prov = {
        r["area_id"]: r["province_code"]
        for r in conn.execute("SELECT area_id, province_code FROM area")
    }

    rows = []
    unmatched = []  # 未命中：全文里查无此名，没有候选官方写法
    with AUDIT.open(encoding="utf-8-sig") as f:
        for a in csv.DictReader(f):
            found = (a.get("found_form") or "").strip()
            if a["status"] == "未命中" or not found:
                if a["status"] == "未命中":
                    unmatched.append((a["area_id"], a["county_code"], a["name"]))
                continue
            official = found
            nf = norm(official)
            src = ""
            if nf:
                for pid, _lp, text in cache.get(area_prov.get(a["area_id"], ""), []):
                    if nf in text:
                        src = pid
                        break
            rows.append({
                "area_id": a["area_id"],
                "county_code": a["county_code"],
                "name_in_db": a["name"],
                "official_form": official,
                "similarity": a.get("similarity") or "",
                "audit_status": a["status"],
                "generic": "是" if is_generic(official) else "否",
                "source_policy": src,
            })

    # 真分歧排前面：非通用词 + 相似度低 + 能定位出处
    def rank(r: dict) -> tuple:
        return (
            0 if r["generic"] == "否" else 1,
            {"未命中": 0, "疑似漂移": 1, "命中（前缀差异）": 2, "命中（后缀差异）": 3}.get(
                r["audit_status"], 9
            ),
            float(r["similarity"] or 1),
        )

    rows.sort(key=rank)

    to_csv.parent.mkdir(parents=True, exist_ok=True)
    with to_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    from collections import Counter

    real = [r for r in rows if r["generic"] == "否"]
    print(f"{len(rows)} 条 -> {to_csv.relative_to(ROOT)}")
    print("状态分布:", dict(Counter(r["audit_status"] for r in rows)))
    print(f"其中非通用词（可能是真分歧）: {len(real)} 条；能定位到出处政策: "
          f"{sum(1 for r in rows if r['source_policy'])}")
    print(f"另有「全文查无此名」{len(unmatched)} 条（无候选写法，需补采或标记待核）")
    print("\n=== 真分歧候选（库内名 ≠ 官方写法，且官方写法不是通用词组）===")
    for r in real[:40]:
        flag = "" if r["source_policy"] else "  [出处未定位]"
        print(f"  {r['area_id']}  {r['name_in_db']}  →  {r['official_form']}"
              f"   [{r['similarity']}] {r['source_policy'] or ''}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
