"""把政策原文里的「附件表格」解析成 `ingest_area_roster` 可用的名单 CSV。

场景：省级名单/资金安排表常以附件表格形式附在方案后（例：河北 P130001 附件3
「2026年和美乡村重点片区奖补项目资金安排表」）。这类表格就是最权威的抽样框，
逐条抄写容易出错，改由脚本解析。

已内置的表格形态（按政策号选择）：
- `HE-130001`：列 = 序号｜市｜县（市、区）｜任务名称｜和美乡村重点片区｜省级资金额度（万元）

输出列与 `ingest_area_roster.py` 对齐，另带 `note` 记录行内附加信息。

    python scripts/roster_from_policy_table.py HE-130001            # 生成名单
    python scripts/roster_from_policy_table.py HE-130001 --dry-run  # 只打印
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
CAND = ROOT / "data" / "stage" / "candidates"

# 政策号 -> (省缩写, policy_id, 表头起始标记, 说明)
FORMS = {
    "HE-130001": ("HE", "P130001", "附件3", "2026年省级乡村振兴专项资金 · 和美乡村重点片区奖补项目"),
}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    key = argv[0]
    dry = "--dry-run" in argv
    if key not in FORMS:
        print(f"未内置表格形态 {key}；可选：{', '.join(FORMS)}")
        return 2
    abbr, pid, marker, label = FORMS[key]

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    pol = con.execute("select title, local_path, issued_ymd, published_ymd, issuer from policy where policy_id=?", (pid,)).fetchone()
    body = (ROOT / pol["local_path"]).read_text(encoding="utf-8", errors="ignore")
    seg = body[body.find(marker):]
    if not seg:
        print(f"{pid} 未找到标记 {marker}")
        return 1

    counties = {r["name"]: r["region_code"] for r in con.execute(
        "select name, region_code from region where level='county' and region_code like ?",
        (abbr and {"HE": "13%", "SD": "37%", "JS": "32%", "ZJ": "33%"}.get(abbr, "%"),))}

    rows = []
    seen_sustained = False       # 表格按「新建块 → 持续支持块」排列，用首个显式「持续支持」行分界
    for line in seg.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [x.strip() for x in line.strip("|").split("|")]
        if len(cells) < 6 or not cells[0].isdigit():
            continue
        seq, city, cty, task, name, money = cells[:6]
        code = counties.get(cty)
        if not code:
            print(f"  !! 第{seq}行县名无法映射：{cty}")
            continue
        # 时间口径：行首「持续支持…」→ unknown；含「新建」→ 当年（year 精度）；
        # 「（同上：新建/持续支持）」两者都含，按表格块位置推断（首个持续块之前算新建）
        t = task.strip()
        if t.startswith("持续支持"):
            seen_sustained = True
            founded, prec = "", "unknown"
        elif "新建" in t:
            founded, prec = pol["issued_ymd"][:4] if pol["issued_ymd"] else "", "year"
        elif seen_sustained:
            founded, prec = "", "unknown"
        else:
            founded, prec = pol["issued_ymd"][:4] if pol["issued_ymd"] else "", "year"
        rows.append({
            "name": name,
            "type_code": "T01",
            "type_primary_note": f"按省级名单补建（{label}）",
            "tags": "和美乡村;重点片区",
            "city_code": "",
            "county_code": code,
            "town_codes": "",
            "scale_villages": "",
            "scale_towns": "",
            "cover_desc": f"{city}{cty}·{name}；省级资金 {money} 万元；任务：{task}（{pid} 附件3 第{seq}条）",
            "status": "运行中",
            "founded_ymd": founded,
            "founded_precision": prec,
            "lead_org": "",
            "issuer": pol["issuer"] or "",
            "summary": f"河北省{label}所列和美乡村重点片区，2026 年省级资金 {money} 万元；"
                       f"依据 {pid}（{pol['issued_ymd'] or pol['published_ymd']}）",
            "source_policy_id": pid,
            "rel": "primary",
        })

    print(f"{key}：解析 {len(rows)} 条（新建 {sum(1 for r in rows if r['founded_precision']=='year')}）")
    for r in rows[:3]:
        print("  样例:", r["name"], "|", r["founded_precision"], "|", r["cover_desc"][:50])
    if dry:
        return 0
    out = CAND / f"area-roster-{abbr}.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"名单 -> {out.relative_to(ROOT)}")
    print("接着跑：ingest_area_roster.py " + abbr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
