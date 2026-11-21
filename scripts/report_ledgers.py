# -*- coding: utf-8 -*-
"""县级名单台账 + 证据欠账报告（两个小报告合并生成，避免再多两个脚本）。

输出：
  reports/县级名单台账.md
  reports/qa/证据欠账-{date}.md
"""
from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    today = date.today().isoformat()
    L: list[str] = []
    add = L.append

    # ---------- 县级名单台账 ----------
    add(f"# 县级名单台账（{today}）\n")
    add("> 来源：`county_roster` 表（`scripts/build_county_roster.py` 生成）。"
        "口径同省/市台账：`status` 五值；`in_db_count` 为库内挂接的片区数。\n")
    rows = list(con.execute("select * from county_roster order by province_code, county_code"))
    dist = Counter(r["status"] for r in rows)
    add("## 一、状态分布\n")
    add("| 状态 | 县数 |")
    add("|---|---|")
    for k in ("matched", "partial", "count_only", "not_area", "none"):
        add(f"| {k} | {dist[k]} |")
    add("")
    add("## 二、逐县明细\n")
    add("| 省 | 县 | 名单名称 | 官方数 | 库内 | 状态 |")
    add("|---|---|---|---|---|---|")
    prov = {r["region_code"]: r["name"] for r in con.execute("select * from region where level='province'")}
    for r in rows:
        add(f"| {prov.get(r['province_code'], r['province_code'])} | {r['county_name']} "
            f"| {(r['roster_name'] or '')[:40]} | {r['official_count'] or '—'} "
            f"| {r['in_db_count'] or 0} | {r['status']} |")
    add("")
    add("## 三、口径说明\n")
    add("- **matched**：名单条目已在库内挂接 primary/support；")
    add("- **partial**：有县级名单类文件，但条目未全部入库；")
    add("- **not_area**：名单对象是村/乡镇层，不是片区（本轮实测县级公开名单多为这一类）；")
    add("- **count_only / none**：只有官方数 / 未见名单。\n")
    (ROOT / "reports" / "县级名单台账.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---------- 证据欠账 ----------
    M: list[str] = []
    m = M.append
    m(f"# 证据欠账（{today}）\n")
    m("> 来源：`evidence_debt` 表（`scripts/build_evidence_debt.py` 生成）。"
        "每一行是一条可执行的补采/修正任务。\n")
    debts = list(con.execute("select * from evidence_debt"))
    by = Counter(r["debt_type"] for r in debts)
    act = sum(1 for r in debts if r["actionable"] == 1)
    m(f"**总计 {len(debts)} 条：可执行 {act} 条 / 结构性 {len(debts) - act} 条**\n")
    m("「可执行」= 有具体动作可做（重锚摘录/补采快照）；「结构性」= 已知口径状态（待核/无依据/村层名单），"
      "不是待办，也不应计入「待清账」。\n")
    m("## 一、按类型\n")
    m("| 类型 | 条数 | 可执行 | 含义 | 处置 |")
    m("|---|---|---|---|---|")
    MEAN = {
        "pending_review": ("status=待核", "补 .gov.cn 原文或官方名单后升 运行中"),
        "no_primary": ("在册非待核但无 primary/support", "补挂政策或降待核"),
        "excerpt_digest": ("摘录为导航性摘要", "按片区名+县名双锚点重锚，或标 digest 降权"),
        "missing_snapshot": ("无本地快照", "probe_dead_sources 重试补采"),
        "county_village": ("县级名单对象是村/乡镇层", "台账维持 not_area，不再重复查"),
    }
    for k, n in by.most_common():
        mean, fix = MEAN.get(k, ("", ""))
        na = sum(1 for r in debts if r["debt_type"] == k and r["actionable"] == 1)
        m(f"| {k} | {n} | {na} | {mean} | {fix} |")
    m("")
    m("## 二、按省分布（前 12）\n")
    m("| 省 | 欠账条数 |")
    m("|---|---|")
    prov = {r["region_code"]: r["name"] for r in con.execute("select * from region where level='province'")}
    pc = Counter(r["province_code"] for r in debts if r["province_code"])
    for code, n in pc.most_common(12):
        m(f"| {prov.get(code, code)} | {n} |")
    m("")
    m("## 三、口径提醒\n")
    m("欠账**不是错误**，是已知缺口。任何对外数字都应声明「有多少条欠账未清」，"
        "不得把欠账当已完成，也不得为清零而删记录。\n")
    (ROOT / "reports" / "qa" / f"证据欠账-{today}.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    print("OK -> reports/县级名单台账.md")
    print(f"OK -> reports/qa/证据欠账-{today}.md")
    print("county_roster", len(rows), "evidence_debt", len(debts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
