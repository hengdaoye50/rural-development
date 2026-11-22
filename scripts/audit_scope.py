# -*- coding: utf-8 -*-
"""口径清洗审计：识别「不是发展意义上片区化单元」的记录（只读）。

用户 2026-11-21 定的目标：只要**中央一号文件意义上「片区化推动乡村振兴」的片区**
——跨村连片、有设立动作或推进机制、以乡村发展为目的。

判据（来自 docs/01 §2–§3）：
  排除：示范村/示范乡镇（E01/E02）、园区/景区/度假区/综合体/小镇/基地/项目（E04/E05）、
        城市控规与国土空间规划分区（E04 旁类）、象征性带廊圈线（应入 belt，E07 例外）。
  保留：名称以「片区/示范片区/片区组团」等为实体名，且能对上乡村振兴口径。

本脚本只产出清单与计数，不改库。输出 `reports/qa/口径外候选-{date}.csv`。
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
OUT = ROOT / "reports" / "qa" / f"口径外候选-{date.today()}.csv"

# 词尾 = 该单元本身是什么；只按词尾判，避免「泰山景区大津口乡乡村振兴片区」被误杀
SUFFIX_DROP = [
    ("园区", "园区"), ("景区", "景区"), ("度假区", "度假区"), ("综合体", "综合体"),
    ("小镇", "小镇"), ("基地", "基地"), ("项目", "项目"), ("中心", "中心"),
    ("示范村", "示范村"), ("精品村", "精品村"), ("示范乡镇", "示范乡镇"), ("示范镇", "示范镇"),
]
SUFFIX_BELT = ["示范带", "带", "廊道", "走廊", "廊", "示范圈", "圈", "环线", "线"]
PLAN = re.compile(r"控制性详细规划|国土空间规划|规划分区|镇级片区|乡镇级片区")


def entity_tail(name: str) -> str:
    """取名称最后 2–4 字，用于判实体类型（去掉尾部括注）。"""
    s = re.sub(r"[（(][^（）()]*[)）]$", "", name or "").strip()
    return s[-4:]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    regions = {r["region_code"]: dict(r) for r in con.execute("select * from region")}
    rows = [dict(r) for r in con.execute("""
        select a.area_id, a.name, a.type_code, a.status, a.setup_kind, a.province_code,
               a.city_code, a.county_code, a.scale_villages, a.cover_desc, a.summary,
               c.caliber_group g, c.in_main_stat m,
               (select count(*) from area_policy_map p where p.area_id=a.area_id
                 and p.rel in ('primary','support')) npol,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel='mention') nmention
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.record_state='active' order by a.area_id""")]

    hits: list[dict] = []

    def add(r, rule, rec, why):
        hits.append({**r, "rule": rule, "rec": rec, "why": why})

    for r in rows:
        name = r["name"] or ""
        tail = entity_tail(name)
        # 1) 规划分区（只看名称；不看 summary，避免把「联合党委」等误杀）
        if PLAN.search(name):
            add(r, "R1 规划分区", "drop", "城市控规/国土空间规划分区，不是乡村振兴片区")
            continue
        # 2) 词尾明确是另一类实体（田园综合体单列）
        if "田园综合体" in name:
            add(r, "R2 田园综合体", "drop", "田园综合体是项目/园区，不是片区（E04）")
            continue
        hit = next((w for w, lab in SUFFIX_DROP if tail.endswith(w) and "片区" not in tail), None)
        if hit:
            add(r, f"R2 实体是{hit}", "drop", f"名称实体是{hit}，不是片区（E04/E05）")
            continue
        # 3) 示范村/乡镇字样（上海「（示范村）片区」是制度内片区，放过）
        if ("示范村" in name or "示范乡镇" in name or "精品村" in name) and "（示范村）片区" not in name:
            add(r, "R3 示范村镇", "drop", "对象是示范村/乡镇，不是片区（E01/E02）")
            continue
        # 4) 象征性带/廊/圈/线
        if any(tail.endswith(w) for w in SUFFIX_BELT) or "示范带" in name:
            add(r, "R4 带廊圈线", "belt", "象征性命名单元，按 area/belt 分界应入 belt（E07 例外）")
            continue
        # 5) 名称不含「片区」且无硬依据、非待核 → 品牌名，证据不足
        if "片区" not in name and r["status"] != "待核" and r["npol"] == 0:
            add(r, "R5 品牌名无依据", "pending", "名称不含「片区」且无 primary/support，先转待核")
            continue
        # 6) 运行中却无 primary/support（状态与证据矛盾）
        if r["status"] == "运行中" and r["npol"] == 0:
            add(r, "R6 运行中无依据", "pending", "状态=运行中 但无 primary/support，按口径应为待核")
            continue
        # 7) county_code 是市级码
        cc = r["county_code"] or ""
        reg = regions.get(cc)
        if reg and reg["level"] != "county":
            add(r, "R7 县码非县级", "check", f"county_code={cc} 是{reg['level']}级码（{reg['name']}）")
            continue
        # 8) 单村覆盖 + 无依据
        if (r["scale_villages"] or 0) == 1 and r["npol"] == 0 and r["status"] != "待核":
            add(r, "R8 单村无依据", "pending", "仅覆盖 1 个村且无 primary/support，疑为村级项目")
            continue
        # 9) 名称含行政区前缀（按 region 名匹配，避免「片区」里的「区」误伤）
        for tok in re.findall(r"^([\u4e00-\u9fa5]{2,6}?(?:省|市|区|县|旗))", name):
            if any(regions[x]["name"] == tok for x in regions if regions[x]["level"] in ("province", "city", "county")):
                add(r, "R9 名称带区划前缀", "name", f"名称以行政区名「{tok}」开头，仅为命名规范问题")
                break

    cnt = Counter(h["rec"] for h in hits)
    by_rule = Counter(h["rule"] for h in hits)
    print(f"全库在册 {len(rows)}｜命中 {len(hits)}｜建议：{dict(cnt)}")
    for tag, n in by_rule.most_common():
        print(f"  {tag}: {n}")
    print("\n样例：")
    seen: Counter = Counter()
    for h in hits:
        if seen[h["rule"]] >= 4:
            continue
        seen[h["rule"]] += 1
        print(f"  [{h['rule']}→{h['rec']}] {h['area_id']} {h['name'][:32]}｜{h['type_code']}｜{h['status']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    cols = ["area_id", "name", "type_code", "status", "g", "m", "province_code", "county_code",
            "scale_villages", "npol", "nmention", "rule", "rec", "why"]
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for h in hits:
            w.writerow({k: h.get(k, "") for k in cols})
    tmp.replace(OUT)
    print(f"\n清单 -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
