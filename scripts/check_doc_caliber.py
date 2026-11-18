"""文档口径守卫：把 README / docs/00 / docs/01 / docs/09 / HANDOVER 里的关键数字
与库内实测值比对，不一致就非零退出。

为什么需要：本项目数字由脚本生成，但文档数字靠手改。2026-11-18 一天内就漂移了两轮
（`docs/01` 作为「数字地基」仍停在 446/621/857，而库已是 470+）。本脚本把「漂移」
变成一条可执行断言，纳入每次批量入库后的固定动作。

设计：
  - 只读，不改任何文件
  - 期望值全部从 `data/db/片区库.sqlite3` 现查（不读 health 报告，避免自我循环）
  - 每条检查给出 文件 / 行号 / 现值 / 期望值；找不到模式也报（说明文档被改写了）
  - 只覆盖最易漂的十来个数字；描述性文字不校验

用法：
  python scripts/check_doc_caliber.py
  python scripts/check_doc_caliber.py --verbose   # 打印通过项
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
DOCS = {
    "README": ROOT / "README.md",
    "00": ROOT / "docs" / "00-整体规划.md",
    "01": ROOT / "docs" / "01-概念界定.md",
    "09": ROOT / "docs" / "09-研究数据与边界声明.md",
    "HANDOVER": ROOT / "HANDOVER.md",
}


def facts() -> dict[str, int | float]:
    con = sqlite3.connect(DB)
    q = lambda s: con.execute(s).fetchone()[0]  # noqa: E731
    active = q("select count(*) from area where record_state='active'")
    pending = q("select count(*) from area where record_state='active' and status='待核'")
    full = active - pending
    main = q("select count(*) from area_caliber where in_main_stat=1")
    cal = {g: q(f"select count(*) from area_caliber where in_scope=1 and caliber_group='{g}'")
           for g in "ABCDE"}
    county_n = q("select count(*) from region where level='county'")
    county_all = q("select count(distinct county_code) from area where record_state='active'")
    county_trusted = q("select count(distinct county_code) from area "
                       "where record_state='active' and status<>'待核'")
    hard = q("select count(*) from area where record_state='active' and status<>'待核' "
             "and exists(select 1 from area_policy_map m where m.area_id=area.area_id "
             "and m.rel in ('primary','support'))")
    return {
        "active": active, "pending": pending, "full": full, "main": main,
        "wide": cal["A"] + cal["B"] + cal["C"],
        "A": cal["A"], "B": cal["B"], "C": cal["C"], "D": cal["D"], "E": cal["E"],
        "macro": q("select count(*) from macro_unit"),
        "nobasis": q("select count(*) from area_caliber where in_scope=1 and "
                     "(caliber_group='E' or (caliber_group='D' and has_hard=0))"),
        "roster_main": q("select count(*) from area_caliber where in_main_stat=1 and setup_kind='roster'"),
        "deploy_main": q("select count(*) from area_caliber where in_main_stat=1 and setup_kind='deployment'"),
        "county_n": county_n, "county_all": county_all, "county_trusted": county_trusted,
        "hard": hard,
        "pct_hard": round(hard / full * 100, 1),
        "pct_county_all": round(county_all / county_n * 100, 1),
        "pct_county_trusted": round(county_trusted / county_n * 100, 1),
    }


# (文档, 正则, 期望键列表)  —— 组数须与键数一致；全部按 int/float 比对
CHECKS: list[tuple[str, str, list[str]]] = [
    # README
    ("README", r"\*\*主统计\*\*（A\+B） \| \*\*(\d+)\*\*", ["main"]),
    ("README", r"宽统计（A\+B\+C） \| \*\*(\d+)\*\*", ["wide"]),
    ("README", r"全量库（在册非待核） \| \*\*(\d+)\*\*", ["full"]),
    ("README", r"\*\*宏观层 M\*\* \| \*\*(\d+)\*\*", ["macro"]),
    ("README", r"active (\d+)（含待核 (\d+)）", ["active", "pending"]),
    ("README", r"\*\*(\d+) 个\*\*有片区建档（([\d.]+)%）", ["county_all", "pct_county_all"]),
    ("README", r"只算可信记录是 \*\*(\d+)\*\*（([\d.]+)%）", ["county_trusted", "pct_county_trusted"]),
    ("README", r"主统计 (\d+) 内为 (\d+) / (\d+)", ["main", "roster_main", "deploy_main"]),
    ("README", r"另有 (\d+) 个片区完全没有", ["nobasis"]),
    # docs/00
    ("00", r"\*\*主统计 A\+B = (\d+)\*\*", ["main"]),
    ("00", r"宽统计 A\+B\+C = (\d+)", ["wide"]),
    ("00", r"全量库 (\d+)（仅描述采集规模）", ["full"]),
    ("00", r"覆盖率 ([\d.]+)%（(\d+)/(\d+)）", ["pct_hard", "hard", "full"]),
    ("00", r"县覆盖 (\d+)/2856 = ([\d.]+)%（可信记录口径 (\d+) = ([\d.]+)%）",
     ["county_all", "pct_county_all", "county_trusted", "pct_county_trusted"]),
    # docs/01
    ("01", r"\| \*\*A\*\* \|[^|]*\| (\d+) \|", ["A"]),
    ("01", r"\| \*\*C\*\* \|[^|]*\| (\d+) \|", ["C"]),
    ("01", r"\| \*\*E\*\* \|[^|]*\| (\d+)（", ["E"]),
    ("01", r"合起来 = (\d+)（在册", ["full"]),
    ("01", r"\| \*\*主统计\*\* \| A \+ B \| \*\*(\d+)\*\*", ["main"]),
    ("01", r"\| \*\*宽统计\*\* \| A \+ B \+ C \| \*\*(\d+)\*\*", ["wide"]),
    ("01", r"\| 全量库 \| 全部 active 且非待核 \| (\d+) \|", ["full"]),
    ("01", r"\| 待核 / 无依据 \| 单列 \| (\d+) / (\d+) \|", ["pending", "nobasis"]),
    ("01", r"三选一明确说：主统计 (\d+) / 宽统计 (\d+) / 全量库 (\d+)", ["main", "wide", "full"]),
    ("01", r"\| \*\*(\d+)\*\*（area (\d+) \+ belt (\d+) − 跨表重名 (\d+)） \| \*\*(\d+)\*\*",
     ["macro", "active", "macro_belt", "macro_dup", "main"]),
    # docs/09
    ("09", r"\*\*主分析样本 N = (\d+)。\*\*", ["main"]),
    ("09", r"\| \*\*主分析样本\*\* \| \*\*(\d+)\*\*", ["main"]),
    ("09", r"\| 含时间不详 \| \*\*(\d+)\*\* \| 有依据但成立时间不可考（(\d+) 条）", ["wide", "C"]),
    ("09", r"\| 待核 \| (\d+) \|", ["pending"]),
    ("09", r"\| 无依据 \| (\d+) \| 无 `primary`", ["nobasis"]),
    ("09", r"([\d][\d ]*)  在册实体片区（active，含 (\d+) 条待核）", ["active", "pending"]),
    ("09", r"(\d+)  非待核", ["full"]),
    ("09", r"(\d+)  有 primary/support 依据", ["wide"]),
    ("09", r"(\d+)  可归时 \+ 可归因", ["main"]),
    ("09", r"\*\*(\d+)/2 856 = ([\d.]+)%\*\* 指", ["county_all", "pct_county_all"]),
    ("09", r"是 \*\*(\d+)/2 856 = ([\d.]+)%\*\*", ["county_trusted", "pct_county_trusted"]),
    ("09", r"`主统计 (\d+)` 只保证", ["main"]),
    ("09", r"分别 为 \*\*(\d+) / (\d+)\*\*|分别为 \*\*(\d+) / (\d+)\*\*", ["roster_main", "deploy_main"]),
    ("09", r"本文的 (\d+) 是\*\*证据可核验", ["main"]),
    ("09", r"\| E 无依据 \| — \| (\d+) \|", ["nobasis"]),
    # HANDOVER
    ("HANDOVER", r"active ([\d ]+) = 计入 (\d+) \+ 待核 (\d+)", ["active", "full", "pending"]),
    ("HANDOVER", r"口径分层（在册非待核 (\d+)）\*\*：A (\d+)｜B (\d+)｜C (\d+)｜D (\d+)｜E (\d+)",
     ["full", "A", "B", "C", "D", "E"]),
    ("HANDOVER", r"\| \*\*主统计 A\+B\*\* \| \*\*(\d+)\*\*", ["main"]),
    ("HANDOVER", r"\| 宽统计 A\+B\+C \| (\d+) \|", ["wide"]),
    ("HANDOVER", r"\| 在册非待核 \| (\d+) \|", ["full"]),
    ("HANDOVER", r"主统计应为 (\d+)", ["main"]),
    ("HANDOVER", r"有命名单元的县 (\d+)／2 856", ["county_all"]),
    ("HANDOVER", r"可信记录口径 \*\*(\d+)／2 856 = ([\d.]+)%\*\*",
     ["county_trusted", "pct_county_trusted"]),
    ("HANDOVER", r"名单型 (\d+)｜`deployment` 部署型 (\d+)", ["roster_main", "deploy_main"]),
]


def main() -> int:
    verbose = "--verbose" in sys.argv
    f = facts()
    # macro 视图里 belt 去重后的数量与重名数
    con = sqlite3.connect(DB)
    f["macro_belt"] = con.execute("select count(*) from macro_unit where kind='belt'").fetchone()[0]
    f["macro_dup"] = con.execute("select count(*) from belt").fetchone()[0] - f["macro_belt"]

    bad = 0
    for doc, pat, keys in CHECKS:
        path = DOCS[doc]
        if not path.exists():
            print(f"✗ {doc}: 文件不存在 {path}")
            bad += 1
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(pat, text, flags=re.M)
        if not m:
            # 09 的 roster/deploy 有两个同义写法，正则已合并；其他找不到说明文档改写了
            print(f"✗ {doc}: 找不到模式 {pat[:48]}")
            bad += 1
            continue
        groups = [g for g in m.groups() if g is not None]
        if len(groups) != len(keys):
            print(f"✗ {doc}: 组数不符 {pat[:48]}")
            bad += 1
            continue
        line = text[:m.start()].count("\n") + 1
        for g, k in zip(groups, keys):
            want = f.get(k)
            if want is None:
                continue
            got = float(g.replace(" ", "")) if isinstance(want, float) else int(g.replace(" ", ""))
            if abs(got - want) > 0.05:
                print(f"✗ {doc}:{line} {k}: 文档 {got} ≠ 库内 {want}")
                bad += 1
            elif verbose:
                print(f"✓ {doc}:{line} {k} = {want}")
    print(f"\n口径数字检查：{'全部一致' if bad == 0 else f'{bad} 处不一致'}")
    if bad:
        print("修法：按库内值重算上述行；或跑 scripts/health_report.py 看最新快照段。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
