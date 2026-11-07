"""生成片区记录修正建议清单（只读，不改数据）。

两类候选：
  1. 区划归属疑似错误：cover_desc/summary 反复出现别的县名，且完全不提自己所在县
  2. 名称疑似漂移：政策全文里的官方写法与库内 name 不一致

输出 reports/qa/area-fix-proposal.md，供人工逐条确认后由 apply_area_fixes.py 执行。

用法：
  python scripts/propose_area_fixes.py
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "qa" / "area-fix-proposal.md"


def main() -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    regions = {r["region_code"]: r for r in cur.execute(
        "select region_code, name, level, parent_code from region")}
    # 只收完整县级名（带行政区划后缀）。裸核心名会误命中普通词：
    # 「大新建片区」→「新建区」、「平原」→「平原县」、「琅琊台」→「琅琊区」
    county_by_name: dict[str, list[str]] = defaultdict(list)
    for code, r in regions.items():
        if r["level"] != "county":
            continue
        county_by_name[r["name"]].append(code)

    areas = list(cur.execute(
        """select area_id, name, county_code, city_code, cover_desc, summary, status
           from area where record_state='active'"""))

    L: list[str] = []
    add = L.append
    add("# 片区记录修正建议\n")
    add("> 只读分析产出。逐条确认后由 `scripts/apply_area_fixes.py` 执行。\n")

    # ---------- 1. 区划归属 ----------
    add("## 一、区划归属疑似错误\n")
    add("判据：`cover_desc`/`summary` 反复提到别的县名，且完全不提自己所在县。\n")
    suspects = []
    for a in areas:
        own = regions.get(a["county_code"])
        if not own:
            continue
        own_name = own["name"]
        own_core = re.sub(r"(自治县|自治旗|县|区|市|旗)$", "", own_name)
        text = f"{a['cover_desc'] or ''} {a['summary'] or ''}"
        own_hits = text.count(own_name) + (text.count(own_core) if len(own_core) >= 2 else 0)
        if own_hits:
            continue
        for nm, codes in county_by_name.items():
            if len(nm) < 3 or nm == own_name:
                continue
            if len(set(codes)) != 1 or codes[0] == a["county_code"]:
                continue
            # 撤县设市/设区会留下同名两码（如龙南县 360727 与龙南市 360782），非归属错误
            if re.sub(r"(县|区|市|旗)$", "", nm) == own_core:
                continue
            cnt = text.count(nm)
            core = re.sub(r"(自治县|自治旗|县|区|市|旗)$", "", nm)
            # 出现两次以上，或县名是片区名前缀（「溧水无想山南片区」← 溧水区）即视为归属线索
            if cnt >= 2 or (cnt >= 1 and core and a["name"].startswith(core)):
                suspects.append({
                    "area_id": a["area_id"], "name": a["name"],
                    "cur": a["county_code"], "cur_name": own_name,
                    "suggest": codes[0], "suggest_name": regions[codes[0]]["name"],
                    "hits": cnt, "note": a["cover_desc"] or "",
                })
                break

    if not suspects:
        add("未发现。\n")
    else:
        add("| area_id | 片区名 | 现归属 | 建议归属 | 文中提及次数 | 原文片段 |")
        add("|---|---|---|---|---|---|")
        for s in suspects:
            add(f"| {s['area_id']} | {s['name']} | {s['cur']} {s['cur_name']} | "
                f"**{s['suggest']} {s['suggest_name']}** | {s['hits']} | {s['note'][:46]} |")
        add("")

    # ---------- 2. 名称漂移 ----------
    add("\n## 二、名称疑似漂移\n")
    audit = ROOT / "reports" / "qa" / "area-name-audit.csv"
    drift = []
    if audit.exists():
        with audit.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("status") == "疑似漂移":
                    drift.append(r)
    if not drift:
        add("未发现（或尚未跑 `audit_area_names.py`）。\n")
    else:
        add("| area_id | 库内写法 | 政策原文写法 | 相似度 | 佐证政策 |")
        add("|---|---|---|---|---|")
        for d in sorted(drift, key=lambda x: -float(x.get("similarity") or 0)):
            pid = ""
            for row in cur.execute(
                """select p.policy_id, p.title from area_policy_map m
                   join policy p on p.policy_id = m.policy_id
                   where m.area_id = ? limit 1""", (d["area_id"],)):
                pid = f"{row['policy_id']} {row['title'][:22]}"
            add(f"| {d['area_id']} | {d['name']} | **{d['found_form']}** | "
                f"{d['similarity']} | {pid} |")
        add("")

    # ---------- 3. 待核 ----------
    add("\n## 三、`status=待核` 记录\n")
    dai = list(cur.execute(
        "select area_id, name, county_code from area where status='待核' and record_state='active'"))
    add(f"共 {len(dai)} 条，统计报告默认排除。\n" if dai else "无。\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"区划归属疑似错误 {len(suspects)} 条；名称疑似漂移 {len(drift)} 条；待核 {len(dai)} 条")
    print(f"-> {OUT}")
    for s in suspects[:10]:
        print(f"   {s['area_id']} {s['name'][:22]}  {s['cur']}→{s['suggest']} ({s['suggest_name']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
