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


def _generic(con, pids: list[str], dry: bool) -> int:
    """通用模式：从任意政策的表格里找「县 + 片区名」，不做逐份定制。

    规则：表格行内含「片区」；从单元格里取最长的含「片区」者为名称；
    县通过 region 表县名匹配（先「XX县/区/市」前缀，再全名包含）。
    """
    counties: dict[str, str] = {}
    for r in con.execute("select region_code, name from region where level='county'"):
        counties[r["name"]] = r["region_code"]
    name_by_core = {}
    for nm, code in counties.items():
        core = re.sub(r'(自治县|自治旗|县|区|市|旗|林区)$', '', nm)
        if len(core) >= 2:
            name_by_core.setdefault(core, code)

    all_rows = []
    for pid in pids:
        p = con.execute("select title, issuer, issued_ymd, published_ymd, local_path from policy where policy_id=?", (pid,)).fetchone()
        if not p:
            print(f"  !! {pid} 不存在")
            continue
        body = (ROOT / p["local_path"]).read_text(encoding="utf-8", errors="ignore")
        got = 0
        for line in body.split("\n"):
            s = line.strip()
            if not s.startswith("|") or "片区" not in s:
                continue
            cells = [x.strip() for x in s.strip("|").split("|")]
            # 名称：含「片区」的最长单元格
            names = [c for c in cells if "片区" in c and 4 <= len(c) <= 40]
            if not names:
                continue
            name = max(names, key=len)
            if re.fullmatch(r'[^区]{0,4}片区', name) or name in ("片区", "重点片区"):
                continue
            # 表格标题不是片区名（如「…建设项目计划表」「…名单」）
            if re.search(r'(计划表|名单|公示|方案|通知|汇总表|安排表|一览表)', name):
                continue
            # 必须是命名单元：以片区类通名结尾；排除公司名与工程项目名
            if not re.search(r'(片区|示范带|示范片|田园综合体|示范区)$', name):
                continue
            if re.search(r'(有限公司|公司|建设发展|建设项目|工程|项目|中心|基地|产业园)', name):
                continue
            # 县：优先名称前缀，其次单元格全名匹配
            code = ""
            m = re.match(r'(.{2,8}?(?:自治县|县|区|市))', name)
            if m:
                code = counties.get(m.group(1), "")
            if not code:
                for c in cells:
                    if c in counties and c != name:
                        code = counties[c]
                        break
            if not code:
                for core, cc in name_by_core.items():
                    if core and core in name:
                        code = cc
                        break
            if not code:
                continue
            all_rows.append({
                "name": name, "type_code": "T01",
                "type_primary_note": f"按政策附件表格补建（{pid}）",
                "tags": "片区", "city_code": "", "county_code": code,
                "town_codes": "", "scale_villages": "", "scale_towns": "",
                "cover_desc": f"{name}；出自 {pid}《{(p['title'] or '')[:30]}》表格行",
                "status": "运行中", "founded_ymd": "", "founded_precision": "unknown",
                "lead_org": "", "issuer": p["issuer"] or "",
                "summary": f"由 {pid}（{p['issued_ymd'] or p['published_ymd'] or '日期不详'}）表格逐条列出",
                "source_policy_id": pid, "rel": "primary",
            })
            got += 1
        print(f"  {pid}: 解析 {got} 条")
    print(f"通用模式合计 {len(all_rows)} 条")
    for r in all_rows[:12]:
        print(f"    {r['county_code']} {r['name'][:34]}")
    if dry or not all_rows:
        return 0
    by_prov = {}
    prov_of = {r["region_code"]: r["region_code"][:2] for r in con.execute(
        "select region_code from region where level='county'")}
    abbr = {"13": "HE", "33": "ZJ", "37": "SD", "32": "JS", "50": "CQ", "51": "SC",
            "61": "SN", "42": "HB", "44": "GD", "41": "HA"}
    for r in all_rows:
        a = abbr.get(prov_of.get(r["county_code"], "")[:2], "")
        if a:
            by_prov.setdefault(a, []).append(r)
    for a, rows in by_prov.items():
        out = CAND / f"area-roster-{a}.csv"
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  名单 -> {out.relative_to(ROOT)}（{len(rows)} 条）")
    return 0


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    if "--generic" in argv:
        pids = argv[argv.index("--generic") + 1].split(",")
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        return _generic(con, pids, dry)
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
