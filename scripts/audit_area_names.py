"""片区名称核对：把 area.name 与政策全文里出现的官方写法对齐。

只读分析，不改任何数据。产出两类清单：
  1. 未命中：片区名在该县政策全文中一次都没出现 —— 可能是名称有误，或该片区无公开文本
  2. 疑似漂移：全文里存在与本片区名高度相似但不相等的写法 —— 极可能是录入误差或双轨命名

用法：
  python scripts/audit_area_names.py
  python scripts/audit_area_names.py --county 330500        # 只看某县
  python scripts/audit_area_names.py --csv reports/qa/area-name-audit.csv
"""
from __future__ import annotations

import csv
import difflib
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# 名称里可剥离的装饰：书名号、间隔号、括号、空格、常见虚词
NOISE = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;·—\-－“”\"'']+")
# 尾部类型词，剥离后用于「干名」比对（舥艚片区 ≈ 舥艚组团片区）
TYPE_TAIL = re.compile(
    r"(乡村振兴示范片区|宜居宜业和美乡村片区|和美乡村片区|乡村振兴片区|示范片区|"
    r"片区组团|组团片区|示范带|示范片|示范圈|共富带|联合体|综合发展片区|片区|组团|带|片|圈)+$"
)


def norm(s: str) -> str:
    return NOISE.sub("", s or "")


def stem(s: str) -> str:
    """去掉尾部类型词，得到可与全文比对的干名（舥艚片区 → 舥艚）。"""
    t = norm(s)
    t2 = TYPE_TAIL.sub("", t)
    return t2 if len(t2) >= 2 else t


def prefixes(s: str, max_len: int = 6):
    """依次去掉开头 2..max_len 个字，应对镇名/街道名不在 region 表的情况。"""
    t = norm(s)
    for i in range(2, min(max_len, len(t) - 1) + 1):
        yield t[i:]


def strip_admin(name: str, admin_terms: set[str]) -> str:
    """剥离开头的行政区名（乐清市北塘片区 → 北塘片区）。"""
    t = norm(name)
    changed = True
    while changed:
        changed = False
        for term in sorted(admin_terms, key=len, reverse=True):
            if term and t.startswith(term) and len(t) > len(term) + 2:
                t = t[len(term):]
                changed = True
                break
    return t


# 从全文里抓「像片区名」的片段
NAME_LIKE = re.compile(
    r"[\u4e00-\u9fa5]{2,12}(?:片区|组团|示范带|示范片|示范圈|共富带|联合体|示范村)"
)


def main() -> int:
    args = sys.argv[1:]
    to_csv = ""
    if "--csv" in args:
        to_csv = args[args.index("--csv") + 1]
    county_filter = ""
    if "--county" in args:
        county_filter = args[args.index("--county") + 1]

    if not DB.exists():
        print(f"DB 不存在: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    areas = cur.execute(
        """select area_id, name, name_norm, county_code, type_code
           from area where record_state='active'
           order by county_code, area_id"""
    ).fetchall()

    # 按县汇总政策全文
    corpus: dict[str, list[str]] = defaultdict(list)
    for r in cur.execute(
        """select p.county_code cc, p.local_path lp
           from policy p where p.county_code is not null and p.county_code <> ''"""
    ):
        p = ROOT / (r["lp"] or "")
        if p.exists():
            corpus[r["cc"]].append(p.read_text(encoding="utf-8"))
    # 挂接到的政策也可能在别的县（省级普适件），补一层
    for r in cur.execute(
        """select a.county_code cc, p.local_path lp
           from area_policy_map m
           join area a on a.area_id = m.area_id and m.entity_type='area'
           join policy p on p.policy_id = m.policy_id"""
    ):
        p = ROOT / (r["lp"] or "")
        if p.exists():
            corpus[r["cc"]].append(p.read_text(encoding="utf-8"))

    by_county: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for a in areas:
        if county_filter and a["county_code"] != county_filter:
            continue
        by_county[a["county_code"]].append(a)

    # 行政区名术语表，用于剥离名称前缀
    admin: dict[str, set[str]] = defaultdict(set)
    for r in cur.execute("select region_code, name, short_name from region"):
        name = r["name"] or ""
        if not name:
            continue
        terms = {name, r["short_name"] or ""}
        for suf in ("省", "市", "县", "区", "自治县", "自治州", "盟", "旗"):
            if name.endswith(suf) and len(name) > len(suf) + 1:
                terms.add(name[: -len(suf)])
        code = r["region_code"]
        # 省市县名在全国范围内都可能成为前缀，放进所有县的术语表
        admin["*"] |= terms
    global_terms = admin["*"]

    rows = []
    n_no_corpus = 0
    for cc, items in by_county.items():
        texts = corpus.get(cc, [])
        if not texts:
            n_no_corpus += len(items)
            for a in items:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "无政策全文", "found_form": "", "similarity": "",
                })
            continue
        joined = " ".join(texts)
        blob = norm(joined)
        candidates = {norm(m.group(0)) for m in NAME_LIKE.finditer(joined)}

        for a in items:
            full = norm(a["name"])
            if not full:
                continue
            # ① 全名命中
            if full in blob:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "命中", "found_form": a["name"], "similarity": "1.00",
                })
                continue
            # ② 剥前缀后再试
            deprefixed = strip_admin(a["name"], global_terms)
            if len(norm(deprefixed)) >= 3 and norm(deprefixed) in blob:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "命中（前缀差异）", "found_form": deprefixed, "similarity": "0.95",
                })
                continue
            # ③ 干名命中（仅后缀/类型词不同）
            st = stem(deprefixed)
            if len(st) >= 2 and st in blob:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "命中（后缀差异）", "found_form": st, "similarity": "0.90",
                })
                continue
            # ③b 逐字去前缀（镇名/街道名不在 region 表，用穷举兜底）
            hit = ""
            for cand in prefixes(deprefixed):
                cs = stem(cand)
                if len(cs) >= 3 and cs in blob:
                    hit = cand
                    break
            if hit:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "命中（前缀差异）", "found_form": hit, "similarity": "0.90",
                })
                continue
            # ④ 仍不中，找最相似的候选写法
            best, ratio = "", 0.0
            for c in candidates:
                r_ = difflib.SequenceMatcher(None, norm(deprefixed), c).ratio()
                if r_ > ratio:
                    best, ratio = c, r_
            if ratio >= 0.6:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "疑似漂移", "found_form": best, "similarity": f"{ratio:.2f}",
                })
            else:
                rows.append({
                    "county_code": cc, "area_id": a["area_id"], "name": a["name"],
                    "status": "未命中", "found_form": "", "similarity": f"{ratio:.2f}",
                })

    stat: dict[str, int] = defaultdict(int)
    for r in rows:
        stat[r["status"]] += 1

    print(f"核对 {len(rows)} 个片区（有政策全文的县 {len([c for c in by_county if corpus.get(c)])} 个）：")
    for k in ("命中", "命中（前缀差异）", "命中（后缀差异）", "疑似漂移", "未命中", "无政策全文"):
        if stat.get(k):
            print(f"  {k:12s} {stat[k]:5d}  ({stat[k] / len(rows) * 100:4.1f}%)")

    drift = [r for r in rows if r["status"] == "疑似漂移"]
    if drift:
        print(f"\n=== 疑似名称漂移 {len(drift)} 条（库内名 → 全文中的近似写法）===")
        for r in sorted(drift, key=lambda x: -float(x["similarity"]))[:40]:
            print(f"  [{r['county_code']}] {r['name']}  →  {r['found_form']}   ({r['similarity']})")

    miss = [r for r in rows if r["status"] == "未命中"]
    if miss:
        print(f"\n=== 全文未命中 {len(miss)} 条（可能是名称有误，或该片区无公开文本）===")
        for r in miss[:25]:
            print(f"  [{r['county_code']}] {r['name']}")

    if to_csv:
        out = ROOT / to_csv
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["county_code", "area_id", "name",
                                              "status", "found_form", "similarity"])
            w.writeheader()
            w.writerows(rows)
        print(f"\n-> {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
