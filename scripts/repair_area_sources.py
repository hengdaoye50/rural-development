"""修复 `area.first_source_id` 悬空：按磁盘上的 raw 证据重建 source 行，无证据的清空指针。

2026-11 扫描发现安徽 5 条 area 的 first_source_id 指向 S340008–S340012，而 source 表里
没有这 5 行。逐一回查 `data/raw/AH/` 后分两类处理：

- **有证据**（A340015 / A340016 / A340017）：从对应政策或 raw 目录重建 source 行，
  `excerpt` 取原文中该片区名附近的逐字片段（≥40 字），`hash_sha256` 按磁盘字节重算
- **无证据**（A340018 茂林镇 / A340019 萧县）：库内没有任何文件提到它们，
  按 docs/03「无 URL/摘录 不入 clean」清空悬空指针，并在报告里登记为需补采

`excerpt` 一律逐字取自原文，不概括、不改写。

    python scripts/repair_area_sources.py --dry-run
    python scripts/repair_area_sources.py
"""
from __future__ import annotations

import csv
import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# area_id -> (新 source_id, 依据类型, 依据键, 用于定位摘录的关键词)
PLAN: dict[str, tuple[str, str, str, str]] = {
    "A340015": ("S340008", "policy", "P340018", "雨山区和美乡村示范片区"),
    "A340016": ("S340009", "policy", "P340006", "百里登源"),
    "A340017": ("S340010", "rawdir", "20260929-jingxian-4pianqu", "示范片区"),
}
NO_EVIDENCE = {
    "A340018": ("S340011", "库内无任何文件提到「茂林镇乡村振兴示范片区」，需补采"),
    "A340019": ("S340012", "库内无任何文件提到「萧县乡村振兴示范片区」，需补采"),
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, cols: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def _excerpt(body: str, keyword: str) -> str:
    i = body.find(keyword)
    if i < 0:
        return ""
    seg = body[max(0, i - 60): i + 120].replace("\r", " ").replace("\n", " ")
    seg = " ".join(seg.split())
    return seg[:200]


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    pol = {r["policy_id"]: r for r in con.execute(
        "select policy_id,title,url,issuer,published_ymd,credibility,local_path,hash_sha256 from policy")}

    s_cols, s_rows = _read(BY_PROV / "AH-source.csv")
    a_cols, a_rows = _read(BY_PROV / "AH-area.csv")
    existing = {r["source_id"] for r in s_rows}

    added, cleared = 0, 0
    for area_id, (new_sid, kind, key, kw) in PLAN.items():
        if kind == "policy":
            p = pol.get(key)
            if not p:
                print(f"  !! {area_id}: 找不到政策 {key}")
                continue
            local = p["local_path"]
            meta = {
                "url": p["url"], "title": p["title"], "publisher": p["issuer"] or "",
                "published_ymd": p["published_ymd"] or "", "credibility": p["credibility"] or "B",
            }
        else:
            d = ROOT / "data" / "raw" / "AH" / key
            import json
            m = json.load(open(d / "meta.json", encoding="utf-8"))
            local = str((d / "原文.md").relative_to(ROOT)).replace("\\", "/")
            meta = {
                "url": m.get("url", ""), "title": m.get("title", ""),
                "publisher": m.get("publisher", ""), "published_ymd": m.get("published_ymd", ""),
                "credibility": m.get("cred", "B"),
            }
        f = ROOT / local
        if not f.exists():
            print(f"  !! {area_id}: 原文缺失 {local}")
            continue
        body = f.read_text(encoding="utf-8", errors="ignore")
        ex = _excerpt(body, kw)
        if len(ex) < 40:
            print(f"  !! {area_id}: 摘录不足 40 字（关键词 {kw} 未命中）")
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if new_sid not in existing:
            s_rows.append({
                "source_id": new_sid, "area_id": area_id,
                "url": meta["url"], "title": meta["title"], "publisher": meta["publisher"],
                "published_ymd": meta["published_ymd"], "excerpt": ex,
                "fetched_at": meta["published_ymd"] or "2026-11-01",
                "credibility": meta["credibility"], "local_path": local, "hash_sha256": digest,
            })
            added += 1
            print(f"  + {new_sid} <- {key}  ({area_id})")
            print(f"      摘录：{ex[:60]}…")
        for r in a_rows:
            if r["area_id"] == area_id:
                r["first_source_id"] = new_sid

    for area_id, (old_sid, why) in NO_EVIDENCE.items():
        for r in a_rows:
            if r["area_id"] == area_id and (r.get("first_source_id") or "") == old_sid:
                r["first_source_id"] = ""
                cleared += 1
                print(f"  - {area_id} 清空悬空指针 {old_sid}：{why}")

    print(f"\n重建 source {added} 条 / 清空悬空指针 {cleared} 条" + ("（dry-run 未写盘）" if dry else ""))
    if not dry and (added or cleared):
        _write(BY_PROV / "AH-source.csv", s_cols, s_rows)
        _write(BY_PROV / "AH-area.csv", a_cols, a_rows)
        print("已写 AH-source.csv / AH-area.csv；接着跑：merge -> build -> validate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
