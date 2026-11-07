"""审计 policy.instruments 是否有全文支撑。

并行采集的最大质量风险不是吞吐，是各 agent 对政策工具的理解不一致。
本脚本按关键词回查 full_text，标出「声称有某工具但正文找不到依据」的记录，
供主控抽样复核时优先看。

用法：
  python scripts/audit_instruments.py                 # 全库
  python scripts/audit_instruments.py --batch POL-ZJ01-policy
  python scripts/audit_instruments.py --csv reports/qa/instruments-audit.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# 每个政策工具的正文证据词（操作性证据，不认单纯提及）
# 判定标准见 docs/07-政策层.md §2.1 / §2.2
EVIDENCE = {
    "财政": r"\d+(\.\d+)?\s*(万元|亿元)|专项资金|专项债|以奖代补|奖补资金|财政衔接|整合涉农资金|安排.{0,8}资金|补助资金",
    "土地": r"用地指标|点状供地|增减挂钩|集体经营性建设用地|土地综合整治|供地|用地计划|用地保障",
    "组织": r"成立.{0,14}(领导小组|专班|指挥部|联席会议|联合党委|党工委)|组建.{0,10}(专班|指挥部|领导小组)|下设办公室|专班|联席会议|推进机制|统筹协调机制|五级书记",
    "考核": r"纳入.{0,10}考核|考核办法|考核细则|星级评定|排名通报|约谈|摘牌|验收标准|实绩考核|动态调整机制|中期评估|评估.{0,10}(不合格|结果|验收)|取消.{0,6}资格|通报批评|年度评估|复核",
    "规划": r"编制.{0,12}规划|规划修编|控制性详细规划|控规|村庄规划|专项规划|两图一表|规划设计方案",
    "人才": r"第一书记|驻村|乡村运营师|选派|引进.{0,8}人才|培育.{0,8}人才|人才引进|返乡创业",
    "金融": r"信贷|担保|保险|产业基金|投融资平台|贷款|贴息|金融机构",
    "产业": r"龙头企业|品牌|产业链|产业园|产业项目|培育.{0,10}产业|招商|新型经营主体",
    "数字": r"数字乡村|智慧农业|数字化平台|信息化平台|智慧乡村|数字技术",
}

# 一份文件编码超过此数视为「疑似全选」，需重读全文收缩
MAX_INSTRUMENTS = 6


def main() -> int:
    args = sys.argv[1:]
    batch = ""
    csv_out = ""
    if "--batch" in args:
        batch = args[args.index("--batch") + 1]
    if "--csv" in args:
        csv_out = args[args.index("--csv") + 1]

    if not DB.exists():
        print(f"DB 不存在: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = "select policy_id, title, instruments, local_path, full_text_chars, created_by from policy"
    params: tuple = ()
    if batch:
        sql += " where created_by = ?"
        params = (batch,)
    rows = cur.execute(sql, params).fetchall()

    flagged = []
    checked = 0
    for r in rows:
        inst = (r["instruments"] or "").strip()
        if not inst:
            continue
        p = ROOT / (r["local_path"] or "")
        if not p.exists():
            flagged.append({
                "policy_id": r["policy_id"], "instrument": "(全文缺失)",
                "issue": f"存档不存在: {r['local_path']}", "title": r["title"],
            })
            continue
        text = p.read_text(encoding="utf-8")
        checked += 1
        toks = [t.strip() for t in inst.split(",") if t.strip()]
        if len(toks) > MAX_INSTRUMENTS:
            flagged.append({
                "policy_id": r["policy_id"], "instrument": f"({len(toks)}个)",
                "issue": f"疑似全选：超过 {MAX_INSTRUMENTS} 个工具，需收缩重编",
                "title": r["title"],
            })
        for tok in toks:
            pat = EVIDENCE.get(tok)
            if not pat:
                flagged.append({
                    "policy_id": r["policy_id"], "instrument": tok,
                    "issue": "未知工具枚举", "title": r["title"],
                })
                continue
            if not re.search(pat, text):
                flagged.append({
                    "policy_id": r["policy_id"], "instrument": tok,
                    "issue": f"全文无匹配关键词 /{pat}/", "title": r["title"],
                })

    print(f"审计 {len(rows)} 条政策，其中 {checked} 条有工具编码")
    if not flagged:
        print("全部工具编码均有全文依据。")
    else:
        print(f"存疑 {len(flagged)} 处：")
        for f in flagged:
            print(f"  {f['policy_id']} [{f['instrument']}] {f['issue']}  {f['title'][:34]}")

    if csv_out:
        out = ROOT / csv_out
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["policy_id", "instrument", "issue", "title"])
            w.writeheader()
            w.writerows(flagged)
        print(f"-> {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
