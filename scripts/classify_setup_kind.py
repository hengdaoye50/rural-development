"""派生 `area.setup_kind`：名单型设立 vs 部署型设立（`docs/01` §10.2）。

为什么要这个字段：2026-11 的裁定是「政府工作报告/专项规划的点名部署也算设立动作」，
但必须与「名单/批复/公布」分列。不拆开，就会得出「县级普遍没有设立文件」的错误结论——
实际上那是县级最普遍的设立方式。

派生规则（机械可复现，不看个案）：
1. 所挂 `primary`/`support` 政策里，只要有**标题含名单/公布/批复/认定/同意/评审结果**
   或**文种属批复/名单/公示/公告**的 → `roster`
2. 否则有 `primary`/`support` 依据 → `deployment`
3. 无 hard 依据 → `unknown`

只写 `data/clean/by_province/*-area.csv`：`area` 是实体表，`merge_by_province` 会用它
整体重建 master，改 master 无意义（与 map 表相反）。

    python scripts/classify_setup_kind.py --dry-run
    python scripts/classify_setup_kind.py
    # 接着跑 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BY_PROV = ROOT / "data" / "clean" / "by_province"
FIELD = "setup_kind"

ROSTER_TITLE_WORDS = ("名单", "批复", "认定", "公布名单", "公布第", "结果公布", "评审结果", "创建名单")
# 注意不要把裸「公布」当名单信号：规划类文件常带「（公布稿）」，会把规划误判成名单型
ROSTER_DOC_TYPES = {"批复", "名单", "公示", "公告"}


def classify(pols: list[tuple[str, str]]) -> str:
    """pols: [(title, doc_type)]"""
    if not pols:
        return "unknown"
    for title, doc_type in pols:
        if any(w in (title or "") for w in ROSTER_TITLE_WORDS):
            return "roster"
        if (doc_type or "") in ROSTER_DOC_TYPES:
            return "roster"
    return "deployment"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        return list(rdr.fieldnames or []), [r for r in rdr if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in header})


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    if not DB.exists():
        print(f"找不到 {DB}（先跑 build_db.py）")
        return 1
    con = sqlite3.connect(DB)
    pol = {r[0]: (r[1], r[2]) for r in con.execute(
        "select policy_id, title, doc_type from policy")}
    links: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for aid, pid in con.execute(
            "select area_id, policy_id from area_policy_map where rel in ('primary','support')"):
        links[aid].append(pol[pid])

    want = {r[0]: classify(links.get(r[0], [])) for r in con.execute("select area_id from area")}
    stat = Counter(want.values())

    changed = 0
    touched = 0
    for path in sorted(BY_PROV.glob("*-area.csv")):
        header, rows = _read(path)
        if not header:
            continue
        if FIELD not in header:
            header = header + [FIELD]
        n = 0
        for r in rows:
            v = want.get(r.get("area_id", ""), "unknown")
            if (r.get(FIELD) or "") != v:
                r[FIELD] = v
                n += 1
        if n:
            touched += 1
            changed += n
            if not dry:
                _write(path, header, rows)
        print(f"{path.name:20s} {len(rows):4d} 行，改动 {n}")

    print()
    print("派生结果（全库）：" + "，".join(f"{k} {v}" for k, v in stat.most_common()))
    print(f"改动 {changed} 行 / {touched} 个文件" + ("（dry-run 未写盘）" if dry else ""))
    if not dry and changed:
        print("接着跑：merge_by_province.py -> build_db.py -> validate_db.py -> health_report.py")
    if not changed:
        print("无改动——已是最新")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
