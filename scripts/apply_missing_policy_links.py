# -*- coding: utf-8 -*-
"""把「正文点名了片区但没挂映射」的候选补成 primary/support（幂等，先 --dry-run）。

数据来源：`reports/qa/missing-policy-links.csv`（由 `audit_missing_policy_links.py` 生成，
判据：片区名去标点后 ≥4 字、同省、正文命中、尚未挂映射）。

rel 判定（宁严勿滥）：
  - 名单/方案/通知/批复/规划/意见/办法/公告/公示/决定 等设立类文件 → `primary`
  - 动态/报告/新闻/总结/答复 等报道类 → `support`（只作佐证）
  - 名称不含「片区」的品牌名 → 一律 `support`

同时把因此获得 primary/support 的「待核」记录升为「运行中」（证据链达标）。

只写 `data/clean/by_province/*-area.csv` 与 `*-area_policy_map.csv`。

用法：
  python scripts/apply_missing_policy_links.py --dry-run
  python scripts/apply_missing_policy_links.py
跑完接 merge_by_province -> build_db -> validate_db -> health_report
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)
CSV_IN = ROOT / "reports" / "qa" / "missing-policy-links.csv"
ESTABLISH = {"名单", "方案", "通知", "批复", "规划", "意见", "办法", "公告", "公示",
             "决定", "指南", "工作要点", "政府批复", "政策文件·行动方案", "立项前公示"}


def read(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
    for r in rows:
        assert set(r) <= set(hdr), f"{p.name}: 字段超出表头 {set(r) - set(hdr)}"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    pol = {r["policy_id"]: dict(r) for r in con.execute(
        "select policy_id, doc_type, source_kind, province_code from policy")}
    st = {r["area_id"]: r["status"] for r in con.execute(
        "select area_id, status from area where record_state='active'")}
    con.close()

    _, rows = read(CSV_IN)
    adds: list[dict] = []
    for r in rows:
        p = pol.get(r["policy_id"])
        if not p:
            continue
        name = r["area_name"]
        keep = "片区" in name
        rel = "primary" if p["doc_type"] in ESTABLISH and keep else "support"
        adds.append({"area_id": r["area_id"], "policy_id": r["policy_id"], "rel": rel,
                     "name": name, "doc_type": p["doc_type"]})
    print(f"候选 {len(rows)}｜拟补 {len(adds)}｜rel={dict(Counter(a['rel'] for a in adds))}")

    # area_id 前两位是省码（A33xxxx），直接映射到 ABBR
    ABBR = {"11": "BJ", "12": "TJ", "13": "HE", "14": "SX", "15": "NM", "21": "LN",
            "22": "JL", "23": "HL", "31": "SH", "32": "JS", "33": "ZJ", "34": "AH",
            "35": "FJ", "36": "JX", "37": "SD", "41": "HA", "42": "HB", "43": "HN",
            "44": "GD", "45": "GX", "46": "HI", "50": "CQ", "51": "SC", "52": "GZ",
            "53": "YN", "54": "XZ", "61": "SN", "62": "GS", "63": "QH", "64": "NX",
            "65": "XJ"}
    by_abbr: dict[str, list[dict]] = defaultdict(list)
    for a in adds:
        by_abbr[ABBR.get(a["area_id"][1:3], "")].append(a)

    today = date.today().isoformat()
    added = upgraded = 0
    for abbr, items in sorted(by_abbr.items()):
        if not abbr:
            print("  ! 无法映射省份：", items[0]["area_id"])
            continue
        pmh, pmrows = read(BP / f"{abbr}-area_policy_map.csv")
        have = {(r["area_id"], r["policy_id"]) for r in pmrows}
        new = [a for a in items if (a["area_id"], a["policy_id"]) not in have]
        for a in new:
            pmrows.append({"area_id": a["area_id"], "policy_id": a["policy_id"],
                           "entity_type": "area", "rel": a["rel"]})
        added += len(new)
        ah, arows = read(BP / f"{abbr}-area.csv")
        up = 0
        for r in arows:
            if r.get("area_id") in {a["area_id"] for a in new} and r.get("status") == "待核":
                r["status"] = "运行中"
                r["updated_at"] = today
                up += 1
        upgraded += up
        print(f"  {abbr}: 补 {len(new)} 条映射，升 {up} 条状态")
        if not dry:
            if new:
                write(BP / f"{abbr}-area_policy_map.csv",
                      list(dict.fromkeys((pmh or []) + ["area_id", "policy_id", "entity_type", "rel"])), pmrows)
            if up:
                write(BP / f"{abbr}-area.csv", ah, arows)
    print(f"共补映射 {added} 条、升状态 {upgraded} 条" + ("（dry-run）" if dry else ""))
    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db -> health_report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
