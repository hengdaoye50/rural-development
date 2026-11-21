# -*- coding: utf-8 -*-
"""数据资产盘点：表、文件、分省资产、口径分布、证据与覆盖；输出 Markdown + CSV。

只读，不改任何数据。用法：python scripts/report_data_assets.py
"""
from __future__ import annotations

import argparse
import csv as _csv
import sqlite3
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"
CAND = ROOT / "data" / "stage" / "candidates"
REPORTS = ROOT / "reports"


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def dir_stat(p: Path) -> tuple[int, int]:
    if not p.exists():
        return 0, 0
    files = [x for x in p.rglob("*") if x.is_file()]
    return len(files), sum(x.stat().st_size for x in files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    today = date.today().isoformat()
    out = Path(args.out) if args.out else ROOT / "reports" / "qa" / f"数据资产盘点-{today}.md"
    csv_out = ROOT / "reports" / "qa" / f"data-assets-{today}.csv"

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = lambda s, p=(): con.execute(s, p).fetchone()[0]  # noqa: E731

    L: list[str] = []
    add = L.append
    add(f"# 数据资产盘点（{today}）\n")
    add("> 全部现查（DB + 文件系统），只读。回答三个问题：**有什么、多少、能不能用**。\n")

    # 1
    add("## 1. 库表规模\n")
    add("| 表/视图 | 行数 | 说明 |")
    add("|---|---|---|")
    NOTE = {
        "area": "片区实体（含待核）", "belt": "象征性命名单元", "source": "第一手证据",
        "policy": "政策文件（.gov.cn）", "event": "生命周期事件", "region": "行政区划",
        "area_policy_map": "片区×政策", "area_region_map": "片区×区划", "area_source_map": "片区×来源",
        "belt_region_map": "带×区划", "province_roster": "省级名单台账", "city_roster": "市级名单台账",
        "area_caliber": "口径视图（五组）", "macro_unit": "M 宏观层视图",
        "unique_active_area": "唯一性视图", "unique_active_belt": "唯一性视图",
    }
    tables = [r[0] for r in con.execute(
        "select name from sqlite_master where type in ('table','view') order by name")]
    for t in tables:
        try:
            n = q("select count(*) from " + t)
        except sqlite3.Error:
            n = -1
        add("| `" + t + "` | " + str(n) + " | " + NOTE.get(t, "") + " |")
    add("")

    # 2
    add("## 2. 文件资产\n")
    add("| 目录 | 文件数 | 体积 | 说明 |")
    add("|---|---|---|---|")
    raw_n, raw_s = dir_stat(RAW)
    add("| `data/raw/` | " + str(raw_n) + " | " + human(raw_s) + " | 原件 + 原文.md + meta.json（只追加） |")
    bp_n, bp_s = dir_stat(CLEAN / "by_province")
    add("| `data/clean/by_province/` | " + str(bp_n) + " | " + human(bp_s) + " | 分省 CSV（并发写入层） |")
    clean_n, clean_s = dir_stat(CLEAN)
    add("| `data/clean/` | " + str(clean_n) + " | " + human(clean_s) + " | master CSV + 分省 |")
    cand_n, cand_s = dir_stat(CAND)
    add("| `data/stage/candidates/` | " + str(cand_n) + " | " + human(cand_s) + " | 候选清单/抽取 JSON/裁定表 |")
    rep_n, rep_s = dir_stat(REPORTS)
    add("| `reports/` | " + str(rep_n) + " | " + human(rep_s) + " | 报告（md/csv） |")
    add("")

    # 3
    add("## 3. 口径分布（视图 `area_caliber`）\n")
    active = q("select count(*) from area where record_state='active'")
    pending = q("select count(*) from area where record_state='active' and status='待核'")
    full = active - pending
    main = q("select count(*) from area_caliber where in_main_stat=1")
    cal = {g: q("select count(*) from area_caliber where in_scope=1 and caliber_group='" + g + "'")
           for g in "ABCDE"}
    setup = [(r[0], r[1]) for r in con.execute(
        "select setup_kind, count(*) from area where record_state='active' group by 1 order by 2 desc")]
    status = [(r[0], r[1]) for r in con.execute(
        "select status, count(*) from area where record_state='active' group by 1 order by 2 desc")]
    add("- active **" + str(active) + "** = 在册非待核 **" + str(full) + "** + 待核 **" + str(pending) + "**")
    add("- 主统计 A+B **" + str(main) + "**；宽统计 A+B+C **" + str(cal["A"] + cal["B"] + cal["C"]) + "**")
    add("- 五组：A " + str(cal["A"]) + "｜B " + str(cal["B"]) + "｜C " + str(cal["C"])
        + "｜D " + str(cal["D"]) + "｜E " + str(cal["E"]))
    setup_txt = "、".join((k or "unknown") + " " + str(v) for k, v in setup)
    add("- 设立方式：" + setup_txt)
    status_txt = "、".join(str(k) + " " + str(v) for k, v in status)
    add("- 状态：" + status_txt)
    add("")

    # 4
    add("## 4. 分省资产\n")
    add("| 省 | 片区(active) | 非待核 | 主统计 | belt | 政策 | 来源 | 有单元县 | 省台账/市台账 |")
    add("|---|---|---|---|---|---|---|---|---|")
    rows = []
    provs = list(con.execute(
        "select region_code, name from region where level='province' order by region_code"))
    for p in provs:
        code = p["region_code"]
        n_area = q("select count(*) from area where province_code=? and record_state='active'", (code,))
        n_full = q("select count(*) from area where province_code=? and record_state='active' "
                   "and status<>'待核'", (code,))
        n_main = q("select count(*) from area_caliber where province_code=? and in_main_stat=1", (code,))
        n_belt = q("select count(*) from belt where province_code=?", (code,))
        n_pol = q("select count(*) from policy where province_code=?", (code,))
        n_src = q("select count(*) from source where area_id like ?", ("A" + code[:2] + "%",))
        n_cty = q("select count(distinct county_code) from area where province_code=? "
                  "and record_state='active'", (code,))
        n_rs = q("select count(*) from province_roster where province_code=?", (code,))
        n_cr = q("select count(*) from city_roster where province_code=?", (code,))
        add("| " + p["name"] + " | " + str(n_area) + " | " + str(n_full) + " | " + str(n_main)
            + " | " + str(n_belt) + " | " + str(n_pol) + " | " + str(n_src)
            + " | " + str(n_cty) + " | " + str(n_rs) + "/" + str(n_cr) + " |")
        rows.append(dict(province_code=code, province=p["name"], area=n_area, full=n_full,
                         main=n_main, belt=n_belt, policy=n_pol, source=n_src,
                         counties=n_cty, province_roster=n_rs, city_roster=n_cr))
    add("")

    # 5
    add("## 5. 覆盖与证据\n")
    county_n = q("select count(*) from region where level='county'")
    county_all = q("select count(distinct county_code) from area where record_state='active'")
    county_trusted = q("select count(distinct county_code) from area where record_state='active' "
                       "and status<>'待核'")
    hard = q("""select count(*) from area where record_state='active' and status<>'待核'
      and exists(select 1 from area_policy_map m where m.area_id=area.area_id and m.rel in ('primary','support'))""")
    add("- 县级单位分母 **" + str(county_n) + "**；有单元县 **" + str(county_all) + "**（"
        + f"{county_all / county_n * 100:.1f}%" + "）；可信记录口径 **" + str(county_trusted)
        + "**（" + f"{county_trusted / county_n * 100:.1f}%" + "）")
    add("- 有 primary/support 依据的在册非待核：**" + str(hard) + "/" + str(full) + "**（"
        + f"{hard / full * 100:.1f}%" + "）")
    add("- 命名单元 M（area+belt 去重）：**" + str(q("select count(*) from macro_unit")) + "**")
    add("")

    # 6
    add("## 6. 名单台账\n")
    for t in ("province_roster", "city_roster"):
        dist = [(r[0], r[1]) for r in con.execute("select status, count(*) from " + t + " group by 1")]
        add("- `" + t + "`：" + "、".join(str(k) + " " + str(v) for k, v in sorted(dist)))
    add("")

    # 7
    add("## 7. 时间分布（在册 active）\n")
    add("| 年份 | 全量 | 其中非待核 |")
    add("|---|---|---|")
    years: Counter = Counter()
    years_full: Counter = Counter()
    for r in con.execute("select founded_ymd, status from area where record_state='active'"):
        y = (r[0] or "")[:4] or "未填"
        years[y] += 1
        if r[1] != "待核":
            years_full[y] += 1
    for y in sorted(years, key=lambda x: (x == "未填", x)):
        add("| " + y + " | " + str(years[y]) + " | " + str(years_full[y]) + " |")
    add("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    with csv_out.open("w", encoding="utf-8-sig", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print("OK ->", out.relative_to(ROOT))
    print("OK ->", csv_out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
