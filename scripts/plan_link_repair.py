"""补链作业清单：把空心片区按「已有线索强度」分级，供定向补依据。

空心片区 = 库内有 area 记录、但 area_policy_map 里没有任何政策。
它们进不了任何机制分析，是当前分析能力的地板。

分五档（线索由强到弱，工时按此排序）：

  A  漏挂型：该县有政策全文，且全文里出现了这个片区名
            → 零采集成本，核实后直接补映射
  B1 形近型：本县全文没有这个名，但有「形近」的名字（相似度≥0.6）
            → 名称校核确认是同一实体后即可补挂
  B2 无名型：本县全文没有任何相近名
            → 疑名称来自媒体稿，或全文不完整，需人核
  C  无文本：该县在库内没有任何政策全文
            → 必须新采（已知县、已知片区名，命中率较高）
  D  弱线索：该省完全没有正文，暂缓

用法：
  python scripts/plan_link_repair.py
  python scripts/plan_link_repair.py --csv reports/qa/link-repair-worklist.csv
"""
from __future__ import annotations

import csv
import difflib
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

PUNCT = re.compile(
    r"[\s\u3000（）()《》〈〉「」" + '""' + r"''【】\[\]、，,。.：:；;·—\-－]+"
)

# 候选片区名：原文中「……片区／示范带／样板带／先导区／田园综合体／片区组团」
CANDIDATE = re.compile(
    r"[\u4e00-\u9fa5]{2,14}(?:片区组团|重点村组团片区|田园综合体|示范片区|样板片区|"
    r"重点片区|精品片区|片区|示范带|样板带|先导区)"
)


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


# 通用词组：形近匹配常把它们当成「片区名」，实际是类别名，不能据此挂接
GENERIC = (
    "重点村组团片区", "片区组团", "田园综合体", "乡村振兴示范片区", "乡村振兴示范带",
    "新乡村示范带", "和美乡村片区", "乡村振兴片区", "示范片区", "样板片区",
    "重点片区", "精品片区", "示范带", "样板带", "先导区", "发展片区", "片区",
)


def strip_generic(s: str) -> str:
    out = s
    for g in GENERIC:
        out = out.replace(g, "")
    return out.strip()


def main() -> int:
    out_csv = ""
    if "--csv" in sys.argv:
        out_csv = sys.argv[sys.argv.index("--csv") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    hollow = conn.execute(
        """
        SELECT area_id, name, province_code, city_code, county_code, type_code, status
        FROM area a
        WHERE a.record_state='active'
          AND NOT EXISTS (SELECT 1 FROM area_policy_map m WHERE m.area_id = a.area_id)
        ORDER BY a.area_id
        """
    ).fetchall()

    # 每县政策全文：同时保留原文（抽候选名用）与归一文本（精确匹配用）
    text_by_county: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    prov_text: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    p_is_province_roster: dict[str, bool] = {}
    for p in conn.execute(
        "SELECT policy_id, province_code, county_code, issuer_level, local_path FROM policy"
    ):
        body = ROOT / p["local_path"]
        if not body.exists():
            continue
        raw = body.read_text(encoding="utf-8")
        item = (p["policy_id"], raw, norm(raw))
        prov_text[p["province_code"]].append(item)
        # 省级/市级发文且没有落到具体县的，视为「名单类」——它可能点名多个县的片区
        p_is_province_roster[p["policy_id"]] = (
            p["issuer_level"] in ("province", "city") and not (p["county_code"] or "").strip()
        )
        if p["county_code"]:
            text_by_county[p["county_code"]].append(item)

    rows = []
    for a in hollow:
        nname = norm(a["name"])
        own = text_by_county.get(a["county_code"], [])
        hit_in = ""
        fuzzy_pid = fuzzy_name = ""
        fuzzy_ratio = 0.0

        if len(nname) >= 4 and own:
            for pid, _raw, t in own:
                if nname in t:
                    hit_in = pid
                    break
        # 扩大到全省所有政策：市级文件、跨县规划、省级名单都可能点名本县片区。
        # 之前只查「本县 + 省级名单」，导致上海 P310023 逐条列了 11 个产业片区
        # 却一直没被检出的情况。
        if not hit_in and len(nname) >= 4:
            for pid, _raw, t in prov_text.get(a["province_code"], []):
                if nname in t:
                    hit_in = pid
                    break

        # 形近匹配只在本县内做。不能扩到全省：区内同名片区很多
        # （「安仁」在龙泉市与建德市都有、「花漾」在海宁市与余杭区都有），
        # 跨县形近匹配会大量假阳性。精确名匹配（上一段）才允许跨县。
        if not hit_in and own and len(nname) >= 4:
            for pid, raw, _t in own:
                for cand in CANDIDATE.findall(raw):
                    r = difflib.SequenceMatcher(None, nname, norm(cand)).ratio()
                    if r > fuzzy_ratio:
                        fuzzy_ratio, fuzzy_pid, fuzzy_name = r, pid, cand
                        if fuzzy_ratio >= 0.95:
                            break

        # 形近名去掉通用词后必须还剩下 ≥3 个字，才是真名字而非类别名
        if hit_in:
            grade, action = "A", "正文已点名，核实后 add_area_policy_link"
        elif fuzzy_ratio >= 0.6 and len(norm(strip_generic(fuzzy_name))) >= 3:
            grade = "B1"
            action = f"形近名「{fuzzy_name}」，名称校核后可挂"
            hit_in = fuzzy_pid
        elif own:
            grade = "B2"
            action = ("仅匹配到类别名「%s」，不算形近" % fuzzy_name if fuzzy_name
                      else "本县全文无相近名，疑名称来自媒体稿或全文不完整")
        else:
            grade = "C" if prov_text.get(a["province_code"]) else "D"
            action = ("本县无全文，需新采（目标明确）" if grade == "C"
                      else "该省无任何全文，暂缓")

        rows.append({
            "grade": grade,
            "area_id": a["area_id"],
            "name": a["name"],
            "province_code": a["province_code"],
            "county_code": a["county_code"],
            "type_code": a["type_code"],
            "status": a["status"],
            "n_policy_in_county": len(own),
            "hit_policy": hit_in,
            "fuzzy_name": fuzzy_name,
            "fuzzy_ratio": f"{fuzzy_ratio:.2f}" if fuzzy_ratio else "",
            "action": action,
        })

    order = {"A": 0, "B1": 1, "B2": 2, "C": 3, "D": 4}
    rows.sort(key=lambda r: (order[r["grade"]], r["province_code"], r["area_id"]))

    dist = Counter(r["grade"] for r in rows)
    print(f"空心片区 {len(rows)} 个")
    for g, label in (
        ("A", "漏挂型（零成本）"),
        ("B1", "形近型（校核后可挂）"),
        ("B2", "无名型（需人核）"),
        ("C", "本县无全文（定向新采）"),
        ("D", "弱线索（暂停）"),
    ):
        print(f"  {g:<3}{label:<22}{dist.get(g, 0):>4}")

    print(f"\n=== B1 形近型（{dist.get('B1', 0)} 条，最值得先做）===")
    for r in rows:
        if r["grade"] == "B1":
            print(f"  {r['area_id']} {r['name'][:26]:<28} ≈「{r['fuzzy_name'][:22]}」"
                  f" {r['fuzzy_ratio']}  {r['hit_policy']}")

    print(f"\n=== C 无文本按省分布（{dist.get('C', 0)} 条）===")
    c_by_prov = Counter(r["province_code"] for r in rows if r["grade"] == "C")
    for p, n in c_by_prov.most_common():
        print(f"  {p} {n}")

    if out_csv:
        p = ROOT / out_csv
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["area_id"])
            w.writeheader()
            w.writerows(rows)
        print(f"\n全量清单 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
