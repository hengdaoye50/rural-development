"""名单覆盖率核对：给定一份省级名单政策，算库内覆盖与缺口。

逆向对账的标准工具。名单来源必须是 .gov.cn 原文且含逐条明细，
否则无法对账（数字口径会在报告里被标为「不可用」）。

判据：
  - 从名单全文按 `--pattern` 抽条目，默认匹配「以县级单元名开头、以片区/示范带/样板带/先导区结尾」的片段
  - 把条目解析到县级码（region.csv 精确/包含匹配，长度优先），避免「秦皇岛市北戴河区」vs「北戴河区」误判
  - 与库内 area + belt 的 county_code 比对

用法：
  python scripts/check_roster_coverage.py P130019
  python scripts/check_roster_coverage.py P420001 --pattern "样板带"
  python scripts/check_roster_coverage.py P210001 --csv reports/qa/roster-LN.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION = ROOT / "data" / "clean" / "region.csv"
DB = ROOT / "data" / "db" / "片区库.sqlite3"

SUFFIX = r"(?:片区|示范带|样板带|先导区|示范片区|示范片|组团片区|片区组团)"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    pid = args[0]
    pattern = None
    out_csv = ""
    if "--pattern" in sys.argv:
        pattern = sys.argv[sys.argv.index("--pattern") + 1]
    if "--csv" in sys.argv:
        out_csv = sys.argv[sys.argv.index("--csv") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    pol = conn.execute(
        "SELECT policy_id, title, province_code, local_path, target_areas FROM policy "
        "WHERE policy_id=?", (pid,)
    ).fetchone()
    if not pol:
        print(f"找不到 policy {pid}")
        return 1
    body = ROOT / pol["local_path"]
    if not body.exists():
        print(f"原文缺失：{pol['local_path']}")
        return 1
    text = re.sub(r"<!--.*?-->", "", body.read_text(encoding="utf-8"))

    # 县名 → 县码（长度优先，避免「秦皇岛市」抢在「北戴河区」前面）
    name2code = {}
    with REGION.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["level"] == "county":
                name2code[r["name"]] = r["region_code"]
    ordered = sorted(name2code, key=len, reverse=True)

    rx = re.compile(pattern) if pattern else re.compile(
        rf"([\u4e00-\u9fa5][^\n。，,：:]{{2,60}}?{SUFFIX})"
    )

    entries = []
    for m in rx.finditer(text):
        e = m.group(1).strip() if m.groups() else m.group(0).strip()
        code = next((name2code[n] for n in ordered if n in e), "")
        entries.append((e, code))

    # 去重（同一片区可能在同一文件出现多次）
    seen, uniq = set(), []
    for e, c in entries:
        if e in seen:
            continue
        seen.add(e)
        uniq.append((e, c))

    prov = pol["province_code"]
    covered = set()
    for tbl in ("area", "belt"):
        for r in conn.execute(
            f"SELECT county_code FROM {tbl} WHERE province_code=? AND record_state='active'", (prov,)
        ):
            if r["county_code"]:
                covered.add(r["county_code"])

    resolved = {c for _e, c in uniq if c}
    miss = sorted(resolved - covered)

    print(f"{pid}  {pol['title'][:56]}")
    print(f"  原文声明条目数 target_areas = {pol['target_areas'] or '（未填）'}")
    print(f"  从全文解析出 {len(uniq)} 条，其中 {len(resolved)} 条能定位到县码")
    print(f"  库内覆盖该省 {len(covered)} 个县")
    print(f"  名单内、库内该县无 → {len(miss)} 个")
    for c in miss:
        nm = next((n for n, cc in name2code.items() if cc == c), c)
        print(f"    - {c} {nm}")

    unresolved = [(e, c) for e, c in uniq if not c]
    if unresolved:
        print(f"  未能解析县码 {len(unresolved)} 条（可能是正文段落或简称）：")
        for e, _c in unresolved[:6]:
            print(f"    ? {e[:58]}")

    if out_csv:
        p = ROOT / out_csv
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["entry", "county_code", "in_db"])
            for e, c in uniq:
                w.writerow([e, c, "是" if c and c in covered else "否"])
        print(f"\n明细 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
