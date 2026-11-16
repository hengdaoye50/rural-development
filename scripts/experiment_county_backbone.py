"""县骨干可行性实验：用已入库的县级政府工作报告，测「县级文件能否抽出片区名」。

不需要新采集——库里已有大量县级政府工作报告。若这些报告里能抽出
「库内没有的片区名」，说明按县穷尽能发现新片区；若几乎抽不出，说明该路线无增量。

口径：
  1. 取 doc_type=报告 且标题含「政府工作报告」的政策
  2. 从中抽「具体命名单元」：一段中文 + 片区/示范片/示范带/先导区/田园综合体 后缀
  3. 排除泛指（若干/各/多个 + 后缀）与类别名（去掉通用词后不足 3 字）
  4. 与该县 area 表中已有名字比对，统计「新名」

用法：
  python scripts/experiment_county_backbone.py
  python scripts/experiment_county_backbone.py --csv reports/qa/county-backbone-experiment.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」" + '""' + r"''【】\[\]、，,。.：:；;·—\-－]+")

NAME_RE = re.compile(
    r"[\u4e00-\u9fa5]{2,14}(?:片区组团|重点村组团片区|田园综合体|示范片区|"
    r"样板片区|重点片区|精品片区|片区|示范带|样板带|先导区|示范片)"
)

GENERIC = (
    "重点村组团片区", "片区组团", "田园综合体", "乡村振兴示范片区", "乡村振兴示范带",
    "新乡村示范带", "和美乡村片区", "乡村振兴片区", "美丽乡村示范片区", "示范片区",
    "样板片区", "重点片区", "精品片区", "乡村振兴建设片", "示范带", "样板带",
    "先导区", "示范片", "片区",
)

VAGUE = re.compile(r"^(若干|各个?|多个|全部|所有|全部|部分|相关|上述|这些|那些|每个|一个|两个|三个|四个|五个|六个|七个|八个|九个|十个)")

# 正则会把前面的动词吞进来（「区委召开英雄山片区」），先把动词前缀切掉
VERB_PREFIX = re.compile(
    r"^(?:区委|县委|市委|党委|政府|召开|推动|推进|加快|打造|建设|完成|落实|围绕|紧扣|"
    r"依托|聚焦|深化|坚持|通过|按照|结合|实现|形成|入选|获批|成为|作为|位于|涉及|"
    r"包括|覆盖|带动|串联|实施|开展|组织|支持|培育|提升|优化|统筹|强化|完善|为|将|对|以|在|是|和|与|及)"
)

# 城市/园区片区的特征词：这些不是乡村片区化单元
URBAN = (
    "控规", "详细规划", "地块", "街区", "社区", "开发区", "工业园区", "产业园",
    "市场", "广场", "交警队", "体校", "医院", "学校", "校区", "站前", "老城",
    "城中村", "棚户", "征收", "拆迁", "商务区", "商圈",
)

# 乡村语境的证据词：候选词前后 60 字内必须出现其一
RURAL_CTX = ("乡村", "振兴", "和美", "示范带", "示范片", "先导区", "田园综合体", "村")


def trim_verb(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        # 切动词前缀
        s = VERB_PREFIX.sub("", s, count=1)
        # 切前导数量词：「个已建成片区」「条绿美示范带」「3个片区」「日完成了片区」
        s = re.sub(r"^(?:[0-9０-９一二三四五六七八九十百千两]+)?(?:个|条|处|片|座|项)", "", s)
        s = re.sub(r"^[0-9０-９一二三四五六七八九十百千两]+", "", s)
    return s


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def strip_generic(s: str) -> str:
    out = norm(s)
    for g in GENERIC:
        out = out.replace(norm(g), "")
    return out


def main() -> int:
    out_csv = ""
    if "--csv" in sys.argv:
        out_csv = sys.argv[sys.argv.index("--csv") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    area_names: dict[str, set[str]] = {}
    for r in conn.execute(
        "SELECT county_code, name FROM area WHERE record_state='active'"
    ):
        area_names.setdefault(r["county_code"], set()).add(norm(r["name"]))

    reports = conn.execute(
        """
        SELECT policy_id, province_code, county_code, title, local_path
        FROM policy
        WHERE doc_type = '报告' AND title LIKE '%政府工作报告%'
          AND county_code IS NOT NULL AND county_code != ''
        ORDER BY county_code
        """
    ).fetchall()

    per_county = []
    for r in reports:
        body = ROOT / r["local_path"]
        if not body.exists():
            continue
        text = body.read_text(encoding="utf-8")
        found: list[str] = []
        for m in NAME_RE.finditer(text):
            cand = trim_verb(m.group(0))
            if VAGUE.match(cand):
                continue
            if len(strip_generic(cand)) < 3:
                continue
            if any(u in cand for u in URBAN):
                continue
            ctx = text[max(0, m.start() - 60): m.end() + 60]
            if not any(k in ctx for k in RURAL_CTX):
                continue
            found.append(cand)
        uniq = sorted(set(found))
        known = area_names.get(r["county_code"], set())
        new = [c for c in uniq if not any(norm(c) in k or k in norm(c) for k in known)]
        per_county.append({
            "county_code": r["county_code"],
            "policy_id": r["policy_id"],
            "title": r["title"][:40],
            "n_names": len(uniq),
            "n_new": len(new),
            "new_names": "、".join(new[:6]),
            "has_area": "是" if r["county_code"] in area_names else "否",
        })

    n = len(per_county)
    hit = [x for x in per_county if x["n_names"] > 0]
    tot_names = sum(x["n_names"] for x in per_county)
    tot_new = sum(x["n_new"] for x in per_county)

    print(f"样本：库内县级政府工作报告 {n} 份\n")
    print(f"抽取成功率：{len(hit)}/{n} 份报告能抽出至少 1 个具体片区名"
          f"（{len(hit)/n*100:.0f}%）" if n else "无样本")
    print(f"新名占比：抽出 {tot_names} 个片区名，其中库内没有的 {tot_new} 个"
          f"（{tot_new/tot_names*100:.0f}%）" if tot_names else "")

    print("\n=== 抽出新名字最多的 12 个县 ===")
    for x in sorted(per_county, key=lambda y: -y["n_new"])[:12]:
        print(f"  {x['county_code']} 共{x['n_names']:>2}个 新{x['n_new']:>2}个 "
              f"[库内有片区:{x['has_area']}] {x['new_names'][:52]}")

    zero = [x for x in per_county if x["n_names"] == 0]
    print(f"\n完全抽不出片区名的县：{len(zero)} 个"
          f"（{len(zero)/n*100:.0f}%）" if n else "")

    if out_csv:
        p = ROOT / out_csv
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(per_county[0].keys()) if per_county else ["county_code"])
            w.writeheader()
            w.writerows(per_county)
        print(f"\n明细 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
