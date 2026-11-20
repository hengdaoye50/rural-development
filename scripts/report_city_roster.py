"""市级名单台账报告：从 `city_roster` 表生成 Markdown。

表 `city_roster` 是权威数据（`data/clean/city_roster.csv`），本脚本只读。
status 语义同 `province_roster`（见 docs/02 §12.1）：
  matched / partial / count_only / not_area / none
「库内已入库」优先取 `in_db_count`（人工核定），空则按 policy_id/source_id 现算。

用法：
  python scripts/report_city_roster.py
  python scripts/report_city_roster.py --province 330000
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "市级名单台账.md"
LABEL = {"matched": "✅ 已对账", "partial": "◐ 部分/待补", "count_only": "○ 仅官方数",
         "not_area": "✕ 非片区类型", "none": "— 库内未见"}


def main() -> int:
    args = sys.argv[1:]
    prov = args[args.index("--province") + 1] if "--province" in args else None
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    where = "where r.province_code = ?" if prov else ""
    params = (prov,) if prov else ()
    rows = list(con.execute(f"""
        select r.*, g.name province_name,
          (select count(*) from area a where a.city_code = r.city_code
             and a.record_state = 'active') n_area,
          (select count(*) from area_policy_map m
             where m.policy_id = r.policy_id and m.rel in ('primary','support')) linked_policy
        from city_roster r
        left join region g on g.region_code = r.province_code
        {where}
        order by r.province_code, r.city_code
    """, params))

    def linked(r) -> int:
        if r["in_db_count"] is not None:
            return int(r["in_db_count"])
        return r["linked_policy"] or 0

    L: list[str] = []
    add = L.append
    title = "市级名单台账" + ("（分省）" if prov else "")
    add(f"# {title}\n")
    add(f"> 数据源：表 `city_roster`（`data/clean/city_roster.csv`）｜生成：{date.today().isoformat()}")
    add("> 回答：**各市有没有一份可逐条对账的市级片区名单**，以及名单 vs 库内已入库。"
        "当前覆盖浙苏鲁 40 市，其余省待补。\n")
    add("## 一、总览\n")
    add("| 状态 | 市数 | 含义 |")
    add("|---|---|---|")
    for k in ("matched", "partial", "count_only", "not_area", "none"):
        n = sum(1 for r in rows if r["status"] == k)
        add(f"| {LABEL[k]} | {n} | {_desc(k)} |")
    add("")
    add("## 二、逐市\n")
    add("| 省 | 市 | 市级名单 | 批次/年度 | 官方数 | 库内已入库 | 库内片区数 | 状态 | 说明 |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        cnt = r["official_count"] if r["official_count"] is not None else "—"
        lk = linked(r)
        warn = ""
        if r["status"] in ("matched", "partial") and r["official_count"] and lk < r["official_count"]:
            warn = " ⚠"
        add(f"| {r['province_name'] or ''} | {r['city_name'] or r['city_code']} | "
            f"{r['roster_name'] or '—'} | {r['roster_scope'] or '—'} | {cnt} | {lk}{warn} | "
            f"{r['n_area']} | {LABEL[r['status']]} | {r['note'] or ''} |")
    add("")
    add("## 三、结论\n")
    add("- **市级名单比省级多得多**：省层多数只有试点县/示范村框架，县以下片区实体主要靠市级名单命名。")
    add("- **已对账 3 市**：湖州（样板片区，6 批文件）、绍兴（精品片区认定）、烟台（2025 市级 6 个，已入库）。")
    add("- **只差原文 1 市**：宿迁 8 个示范片区已在报道里逐条列出，方案原文入库即可落 8 条。")
    add("- **库内未见不等于没有**：34 市标 `none` 只表示「库里没有市级名单文件」，未做站外检索。\n")
    add("## 四、下一批动作\n")
    add("1. 宿迁：《高质量建设宜居宜业和美乡村的实施方案》原文 → 8 条入库")
    add("2. 浙苏鲁其余市：按「市农业农村局 名单/公布/认定」逐市检索（优先湖州/绍兴同类「样板片区/精品片区」）")
    add("3. 把 `city_roster` 扩到全部 333 个地级行政区\n")
    add("## 五、复现\n")
    add("```powershell\npython scripts/report_city_roster.py\n```")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK -> {OUT.relative_to(ROOT)}")
    print("状态分布:", {k: sum(1 for r in rows if r['status'] == k) for k in LABEL})
    return 0


def _desc(k: str) -> str:
    return {
        "matched": "市级名单在库且条目已挂接",
        "partial": "名单类文件在库但非完整名单/未入库",
        "count_only": "只有官方数字，名单未取得",
        "not_area": "市级名单对象不是县以下片区",
        "none": "库内未见市级名单文件（未做站外检索）",
    }[k]


if __name__ == "__main__":
    sys.exit(main())
