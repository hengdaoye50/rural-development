"""覆盖率缺口定位：把「两千多个零单元县」收敛成「手里已有证据的几十到几百个县」。

背景（2026-11 实测）：
- 库内 1699 份全文里**自动抽片区名不可靠**——正文正则的产出七成是城市控规分区
  （「海棠湾片区」「亚龙湾片区」）或句子碎片（「支持省级和美乡村重点片区」），标题正则
  精度高但产量只有 7 条。所以本脚本**不抽名、不建档**，只回答一件事：
  哪些零单元县的证据文件已经在库里，值得逐份精读。
- 分母换口径无益：市辖区覆盖率（193/974=19.8%）反而高于非市辖区（326/1882=17.3%），
  所以「排除城市辖区」不能改善覆盖率，别再试。

分层（确定性从高到低）：
- T1 该县本级发文，但库里零单元——文件是它自己发的，读一份就能判定有无
- T2 名单/规划/批复/公告类文件里出现该县**全名**且正文含片区类词——入库入口精度最高
- T3 仅动态/报告/总结类文件提及——信号弱，最后做

    python scripts/find_coverage_gaps.py
    python scripts/find_coverage_gaps.py --csv reports/gaps/coverage-gaps.csv
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT_MD = ROOT / "reports" / "gaps" / "coverage-gaps.md"
OUT_CSV = ROOT / "reports" / "gaps" / "coverage-gaps.csv"

STRONG_TYPES = {"名单", "规划", "批复", "公告", "公示", "通知", "意见", "办法", "方案"}
UNIT_WORDS = ("片区", "示范带", "示范片", "田园综合体")


def main(argv: list[str]) -> int:
    csv_path = OUT_CSV
    if "--csv" in argv:
        i = argv.index("--csv")
        csv_path = ROOT / argv[i + 1]
    if not DB.exists():
        print(f"找不到 {DB}")
        return 1
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    cty = {r["region_code"]: r["name"] for r in con.execute(
        "select region_code, name from region where level='county'")}
    prov = {r["region_code"]: (r["short_name"] or r["name"]) for r in con.execute(
        "select region_code, name, short_name from region where level='province'")}
    covered = {r[0] for r in con.execute(
        "select distinct county_code from macro_unit where county_code is not null and county_code<>''")}
    uncovered = set(cty) - covered

    pol = list(con.execute(
        "select policy_id, title, doc_type, local_path, county_code, province_code "
        "from policy where coalesce(local_path,'')<>''"))
    own = defaultdict(list)
    for r in pol:
        if r["county_code"]:
            own[r["county_code"]].append(r)

    full = {nm: cd for cd, nm in cty.items() if nm and len(nm) >= 3}
    mention = defaultdict(list)
    policy_spread: dict[str, set[str]] = defaultdict(set)
    scanned = 0
    WINDOW = 120
    for r in pol:
        p = ROOT / r["local_path"]
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        # 只看片区类词出现的位置：县名必须落在附近才算「该县有自己的片区表述」，
        # 否则相邻县的规划、省级规划里的顺带点名都会算进来（临平区曾被桐乡市规划命中）
        anchors = []
        for w in UNIT_WORDS:
            start = 0
            while True:
                i = t.find(w, start)
                if i < 0:
                    break
                anchors.append(i)
                start = i + 1
        if not anchors:
            continue
        scanned += 1
        for nm, cd in full.items():
            if cd not in uncovered or cd[:2] != (r["province_code"] or "")[:2]:
                continue
            start = 0
            while True:
                i = t.find(nm, start)
                if i < 0:
                    break
                start = i + 1
                if any(abs(a - i) <= WINDOW for a in anchors):
                    mention[cd].append(r)
                    policy_spread[r["policy_id"]].add(cd)
                    break

    rows = []
    for cd in uncovered:
        own_docs = own.get(cd, [])
        men = mention.get(cd, [])
        strong = [d for d in men if (d["doc_type"] or "") in STRONG_TYPES]
        if own_docs:
            tier, signal = "T1", own_docs
        elif strong:
            tier, signal = "T2", strong
        elif men:
            tier, signal = "T3", men
        else:
            continue
        rows.append({
            "county_code": cd,
            "county_name": cty[cd],
            "province": prov.get(cd[:2] + "0000", cd[:2]),
            "tier": tier,
            "own_docs": len(own_docs),
            "signal_docs": len(signal),
            "sample": "; ".join(f"{d['policy_id']}:{(d['title'] or '')[:34]}" for d in signal[:3]),
        })
    rows.sort(key=lambda r: (r["tier"], -r["signal_docs"], r["county_code"]))

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    tiers = Counter(r["tier"] for r in rows)
    tier_prov = {t: Counter(r["province"] for r in rows if r["tier"] == t).most_common(6) for t in tiers}
    tot_cty = len(cty)

    lines = [
        "# 覆盖率缺口定位",
        "",
        "> 生成：`scripts/find_coverage_gaps.py`｜明细 `reports/gaps/coverage-gaps.csv`",
        "",
        "## 一、先看三个负结果（省得再试）",
        "",
        "| 试过的路 | 结果 |",
        "|---|---|",
        f"| 全库正文正则抽片区名 | **不可用**：1699 份文本扫出 87 个候选，七成是城市控规分区"
        f"（三亚「海棠湾片区」）或句子碎片（「支持省级和美乡村重点片区」） |",
        f"| 标题正则抽（县名+片区名同现） | **精度高但产量低**：仅 7 条 / 3 个县。"
        f"因为库里绝大多数是动态与报告，不是一区一规划的载体 |",
        f"| 分母换成非市辖区 | **无益**：市辖区覆盖率 193/974=19.8%，"
        f"非市辖区 326/1882=17.3%，排除城市辖区反而更低 |",
        "",
        "结论：**覆盖率提升的瓶颈是入口，不是算法。** 自动抽名会把概念界定炸掉，"
        "只能「先定位文件、再逐份精读」。",
        "",
        "## 二、作业面：{} 个零单元县里有 {} 个手里已有证据".format(len(uncovered), len(rows)),
        "",
        f"零单元县共 {len(uncovered)} 个（县级单位 {tot_cty}，已覆盖 {len(covered)}）。"
        f"扫描 {scanned} 份含片区类词的全文后，可定位出 {len(rows)} 个县有证据在手：",
        "",
        "| 层 | 县数 | 含义 | 处理方式 |",
        "|---|---|---|---|",
        f"| **T1** | {tiers.get('T1', 0)} | 该县本级发文但库里零单元 | 读 1 份本级文件即可判定，成本最低 |",
        f"| **T2** | {tiers.get('T2', 0)} | 名单/规划/批复/公告类文件含该县全名 | 逐份精读，入库入口精度最高 |",
        f"| **T3** | {tiers.get('T3', 0)} | 仅动态/报告/总结类提及 | 信号弱，最后做 |",
        "",
        "各省分布：",
        "",
        "| 层 | 主要省份（县数） |",
        "|---|---|",
    ]
    for t in ("T1", "T2", "T3"):
        if tier_prov.get(t):
            lines.append(f"| {t} | " + "、".join(f"{k} {v}" for k, v in tier_prov[t]) + " |")
    lines += [
        "",
        "## 三、高杠杆文件：一篇覆盖多县，先读这些",
        "",
        "同一份文件命中多个零单元县，说明它是「逐条列各县片区」的名单/方案类文件。"
        "**读一份等于覆盖 N 个县**，这是提升覆盖率最快的入口，优先于按省摊派。",
        "",
        "| policy_id | 命中零单元县数 | 文件 |",
        "|---|---|---|",
    ]
    pol_title = {r["policy_id"]: r["title"] for r in pol}
    for pid, cds in sorted(policy_spread.items(), key=lambda x: -len(x[1]))[:12]:
        if len(cds) < 2:
            continue
        nm = "、".join(cty[c] for c in sorted(cds)[:6])
        more = f" 等 {len(cds)} 县" if len(cds) > 6 else ""
        lines.append(f"| {pid} | {len(cds)} | {(pol_title.get(pid) or '')[:52]}<br>{nm}{more} |")
    lines += [
        "",
        "读这类文件时只做一件事：把正文里**逐条列出的单元名**抄进 "
        "`data/stage/candidates/area-roster-{ABBR}.csv`，走 `scripts/ingest_area_roster.py` 入库。"
        "不要在正文里做正则批量抽名——实测七成是城市控规分区。",
        "",
        "**注意命中数会偏高**：片区规划的正文常在「区位」段落里顺带点到相邻县"
        "（安州区的规划因此把涪城区、游仙区一起命中）。所以这张表用来排**阅读顺序**，"
        "不能用来算覆盖增量——真实增量要读完文件才知道。",
        "",
        "## 四、已验证的样板：四川安州区",
        "",
        "T2 层里已经人工核过一例，可以当精读流程的模板：",
        "",
        "`510705 安州区` 库内零单元，但库里有 **4 份一区一规划的全文**：",
        "",
        "| policy_id | 片区名 | 全文汉字 |",
        "|---|---|---|",
        "| P510001 | 安昌河都市经济发展片区 | 59,134 |",
        "| P510003 | 干河子优质农业发展片区 | 63,288 |",
        "| P510004 | 凯江城乡融合发展片区 | 72,092 |",
        "| P510002 | 千佛山生态康养文旅片区 | 1,794（仅公布稿启事） |",
        "",
        "这 4 个片区名是从**文件名**取的，不是正则猜的；规划全文已在磁盘上，"
        "每个片区的「规划范围（涉乡镇/村）」都在正文里。所以这类县的建档成本约等于"
        "「读 4 份文件 + 填 4 行 CSV」，走 `scripts/ingest_area_roster.py` 即可入库。",
        "",
        "## 五、下一步怎么用这份清单",
        "",
        "1. 先做 **T1 的全部**（含江西 23 个赣州县，已知是「报告不点名片区」的查无情形，"
        "读一份即可留证并关闭）",
        "2. 再做 **T2**，按省分批：四川、浙江、山东这类「一区一规划」载体多的省优先，"
        "因为这些省的文件里直接写全了片区名与所辖村",
        "3. **T3 不做**，除非 T1/T2 清完后仍有余力——它们是动态报道的顺带提及，"
        "按 docs/01 大概率不满足「有设立动作」",
        "",
        "**注意**：本清单只解决「分子」，不解决「分母」。分母仍是未知的——"
        "要算真实漏采率，只能靠省级名单对账或分层抽样，两者都需要采集通道。",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"零单元县 {len(uncovered)}；有证据在手 {len(rows)}"
          f"（T1 {tiers.get('T1', 0)} / T2 {tiers.get('T2', 0)} / T3 {tiers.get('T3', 0)}）")
    print(f"OK -> {OUT_MD.relative_to(ROOT)} / {csv_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
