"""省级名单台账报告：从 `province_roster` 表生成 Markdown，并现算「库内已入库数」。

表 `province_roster` 是权威数据（`data/clean/province_roster.csv`），本脚本只读：
  - `policy_id` 有值 → 按 `area_policy_map` 的 primary/support 数计「库内已入库」
  - `source_id` 有值（只有媒体来源）→ 按 `area_source_map` 数
  - 都没有 → 0（并提示）

状态枚举（docs/02）：
  matched   已对账（名单条数与库内可对应）
  partial   部分/待补官方（名单在库但未全入库，或只有媒体来源）
  count_only 仅官方数（名单未公开/未取得）
  not_area  省级名单不是片区类型（示范村/乡镇/精品村等）
  none      未见省级名单

用法：
  python scripts/report_province_roster.py
  python scripts/report_province_roster.py --md reports/省级名单台账.md
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "省级名单台账.md"
LABEL = {"matched": "✅ 已对账", "partial": "◐ 部分/待补", "count_only": "○ 仅官方数",
         "not_area": "✕ 非片区类型", "none": "— 未见"}


def main() -> int:
    args = sys.argv[1:]
    out = Path(args[args.index("--md") + 1]) if "--md" in args else OUT
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = list(con.execute("""
        select r.*, g.name province_name,
          (select count(*) from area_policy_map m
             where m.policy_id = r.policy_id and m.rel in ('primary','support')) linked_policy,
          (select count(*) from area_source_map x
             where x.source_id = r.source_id) linked_source
        from province_roster r
        left join region g on g.region_code = r.province_code
        order by r.province_code
    """))
    def linked(r) -> int:
        if r["in_db_count"] is not None:
            return int(r["in_db_count"])
        return r["linked_policy"] or r["linked_source"] or 0

    L: list[str] = []
    add = L.append
    add("# 省级名单台账（省级层口径）\n")
    add(f"> 数据源：表 `province_roster`（`data/clean/province_roster.csv`）｜生成：{date.today().isoformat()}")
    add("> 一句话：**每省省级层面到底有没有一份可逐条对账的片区名单**，以及名单条数 vs 库内已入库数。\n")
    add("## 一、总览\n")
    add("| 状态 | 省数 | 含义 |")
    add("|---|---|---|")
    for k in ("matched", "partial", "count_only", "not_area", "none"):
        n = sum(1 for r in rows if r["status"] == k)
        add(f"| {LABEL[k]} | {n} | {_desc(k)} |")
    add("")
    add("## 二、逐省\n")
    add("| 省 | 省级名单 | 批次/年度 | 官方数 | 口径 | 库内已入库 | 状态 | 说明 |")
    add("|---|---|---|---|---|---|---|---|")
    for r in rows:
        cnt = r["official_count"] if r["official_count"] is not None else "—"
        basis = r["count_basis"] or "—"
        lk = linked(r)
        warn = ""
        if r["status"] in ("matched", "partial") and r["official_count"] and lk < r["official_count"]:
            warn = " ⚠"
        add(f"| {r['province_name'] or r['province_code']} | {r['roster_name'] or '—'} | "
            f"{r['roster_scope'] or '—'} | {cnt} | {basis} | {lk}{warn} | {LABEL[r['status']]} | "
            f"{r['note'] or ''} |")
    add("")
    add("## 三、能支撑什么 / 不能支撑什么\n")
    add("- **可对账的省**（matched）：可以用「官方名单条数」做分母算漏采率。")
    add("- **部分/待补**（partial）：只能报「名单条数 vs 库内数」，差多少要注明是证据缺口还是口径差。")
    add("- **仅官方数**（count_only）：只有数字、没有逐条名单，**不能算漏采率**，只能做量级对照。")
    add("- **非片区类型**（not_area）：省级公布的是示范村/乡镇/精品村，按 `docs/01` §3 不收；")
    add("  若研究需要，应另建「省级示范村」对照表，不得与 `area` 混算。")
    add("- **未见**（none）：不代表不存在，只代表尚未检索到公开名单。\n")
    add("## 四、下一批动作\n")
    cand = [r for r in rows if r["status"] in ("partial", "count_only", "none")]
    for r in cand:
        if r["status"] == "partial":
            add(f"- **{r['province_name']}**：{r['note']}")
        elif r["status"] == "count_only":
            add(f"- **{r['province_name']}**：拿到逐条名单即可从「仅官方数」升级为「可对账」")
        else:
            add(f"- **{r['province_name']}**：检索省农业农村厅「片区/示范带/样板带」名单")
    add("")
    add("## 五、复现\n")
    add("```powershell\npython scripts/report_province_roster.py\n```")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK -> {out.relative_to(ROOT)}")
    print("状态分布:", {k: sum(1 for r in rows if r['status'] == k) for k in LABEL})
    return 0


def _desc(k: str) -> str:
    return {
        "matched": "名单条数与库内可逐条对应",
        "partial": "名单在库但未全入库，或只有媒体来源",
        "count_only": "只有官方数字，名单未公开/未取得",
        "not_area": "省级公布的是示范村/乡镇/精品村，非片区",
        "none": "尚未检索到省级名单",
    }[k]


if __name__ == "__main__":
    sys.exit(main())
