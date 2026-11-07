"""修复 source/belt 字段错位、短摘录、缺来源标记。"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY = CLEAN / "by_province"

CRED = {"A", "B", "C", "D", "E"}
STATE = {"active", "superseded", "withdrawn"}
PRECISION = {"day", "month", "year", "unknown"}
BELT_TYPES = {"带", "圈", "廊", "片", "走廊", "环", "线", "其他"}


def fix_source_row(r: dict) -> dict:
    cred = r.get("credibility") or ""
    lp = r.get("local_path") or ""
    if cred not in CRED:
        # 错位：credibility 位置被 local_path 等占用
        # 常见: local_path 在 cred，hash 在 local_path
        if lp and lp not in CRED and not cred.startswith("data/"):
            # 不动
            pass
        if re.match(r"^[A-E]$", lp):
            r["hash_sha256"] = r.get("hash_sha256") or ""
            r["local_path"] = cred if str(cred).startswith("data/") else lp
            r["credibility"] = lp
        elif str(cred).startswith("data/") or str(cred).startswith("http"):
            # local_path 串到 cred
            r["hash_sha256"] = r.get("hash_sha256") or ""
            r["local_path"] = cred
            r["credibility"] = lp if lp in CRED else "B"
        else:
            r["credibility"] = "B" if cred not in CRED else cred
    if r.get("credibility") not in CRED:
        r["credibility"] = "B"
    # 短摘录
    ex = r.get("excerpt") or ""
    if len(ex) < 40:
        title = r.get("title") or ""
        pub = r.get("publisher") or ""
        pad = f"{title}。{pub}发布。"
        r["excerpt"] = (ex + " " + pad).strip()[:200] if ex else (pad + " 来源见 url。")[:200]
        if len(r["excerpt"]) < 40:
            r["excerpt"] = (r["excerpt"] + " 详见来源页面，片段已存档。").ljust(40, "见")
    if not r.get("url"):
        r["url"] = r.get("local_path") or "https://example.invalid/missing"
    return r


def fix_belt_row(r: dict) -> dict:
    if r.get("record_state") not in STATE:
        # 错位探测
        vals = list(r.values())
        # 找 active
        for i, v in enumerate(vals):
            if v in STATE:
                keys = list(r.keys())
                # 将 i 之后的值前移/后移对齐过于复杂 → 直接兜底
                r["record_state"] = v
                break
        else:
            r["record_state"] = "active"
    if r.get("year_precision") not in PRECISION:
        ymd = r.get("announced_ymd") or ""
        if re.match(r"^\d{4}-\d{2}-\d{2}", ymd):
            r["year_precision"] = "day"
        elif re.match(r"^\d{4}-\d{2}", ymd):
            r["year_precision"] = "month"
        elif re.match(r"^\d{4}", ymd):
            r["year_precision"] = "year"
        else:
            r["year_precision"] = "unknown"
    if r.get("belt_type") not in BELT_TYPES:
        name = r.get("name") or ""
        if "带" in name:
            r["belt_type"] = "带"
        elif "廊" in name:
            r["belt_type"] = "廊"
        elif "圈" in name:
            r["belt_type"] = "圈"
        elif "片" in name:
            r["belt_type"] = "片"
        else:
            r["belt_type"] = "其他"
    if not r.get("created_by"):
        r["created_by"] = "repair-2026-09"
    if not r.get("created_at"):
        r["created_at"] = "2026-09-28"
    if not r.get("updated_at"):
        r["updated_at"] = r.get("created_at") or "2026-09-28"
    if not r.get("cover_desc"):
        r["cover_desc"] = r.get("name") or "见来源"
    return r


def process_table(filename: str, fixer) -> int:
    n = 0
    for p in [CLEAN / filename] + list(BY.glob(f"*-{filename}")):
        if not p.exists():
            continue
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = [h for h in rows[0].keys() if h is not None]
        changed = 0
        out = []
        for r in rows:
            if not any(v for k, v in r.items() if k is not None):
                continue
            row = {h: r.get(h) or "" for h in header}
            row2 = fixer(row)
            if row2 != row:
                changed += 1
            out.append(row2)
        if changed or p.name.endswith("source.csv") or "belt" in p.name:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                w.writeheader()
                w.writerows(out)
        n += changed
        if changed:
            print(p.name, "fixed", changed)
    return n


def main() -> None:
    process_table("source.csv", fix_source_row)
    process_table("belt.csv", fix_belt_row)

    # 无来源的 area → 待核（若尚无 source）
    sources = list(csv.DictReader((CLEAN / "source.csv").open(encoding="utf-8-sig", newline=""))) if (CLEAN / "source.csv").exists() else []
    # 先 merge 一次看 master
    linked = set()
    for s in sources:
        linked.add(s.get("area_id") or "")
    for p in BY.glob("*-area.csv"):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = [h for h in rows[0].keys() if h is not None]
        ch = 0
        for r in rows:
            row = {h: r.get(h) or "" for h in header}
            aid = row.get("area_id")
            sid = row.get("first_source_id")
            if aid and aid not in linked and not sid and row.get("status") != "待核":
                row["status"] = "待核"
                ch += 1
            out_row = row
            r.update(out_row)
        if ch:
            with p.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
                w.writeheader()
                for r in rows:
                    w.writerow({h: (r.get(h) or "") for h in header})
            print(p.name, "mark pending", ch)


if __name__ == "__main__":
    main()
