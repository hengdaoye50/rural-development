"""将 source 中已有摘录落盘为 raw 证据快照（不补造内容，只固化已记录证据）。"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"


def slugify(text: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", text)[:40].strip("-")
    return s or "untitled"


def main() -> None:
    path = CLEAN / "source.csv"
    sources = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    header = list(sources[0].keys())
    changed = 0
    for s in sources:
        if s.get("local_path"):
            continue
        sid = s.get("source_id") or "unknown"
        title = s.get("title") or sid
        # 省份目录
        ref = s.get("area_id") or ""
        prov = "other"
        if ref.startswith("A32") or ref.startswith("B32") or sid.startswith("S32"):
            prov = "JS"
        elif ref.startswith("A33") or ref.startswith("B33") or sid.startswith("S0") or sid.startswith("S33"):
            prov = "330000-浙江"
        elif ref.startswith("A37") or ref.startswith("B37") or sid.startswith("S37"):
            prov = "SD"
        folder = RAW / prov / f"excerpt-{sid}-{slugify(title)}"
        folder.mkdir(parents=True, exist_ok=True)
        meta = {
            "source_id": sid,
            "url": s.get("url") or "",
            "title": title,
            "publisher": s.get("publisher") or "",
            "published_ymd": s.get("published_ymd") or "",
            "fetched_at": s.get("fetched_at") or "",
            "credibility": s.get("credibility") or "",
            "kind": "excerpt-snapshot",
        }
        (folder / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        body = [
            f"# {title}",
            "",
            f"- source_id: {sid}",
            f"- url: {s.get('url') or ''}",
            f"- publisher: {s.get('publisher') or ''}",
            f"- published: {s.get('published_ymd') or ''}",
            f"- credibility: {s.get('credibility') or ''}",
            "",
            "## 摘录",
            s.get("excerpt") or "",
            "",
            "> 注：本快照由入库摘录固化生成，非全文抓取。",
        ]
        (folder / "原文.md").write_text("\n".join(body), encoding="utf-8")
        s["local_path"] = str(folder.relative_to(ROOT)).replace("\\", "/")
        changed += 1

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(sources)
    print("excerpt snapshots", changed)

    # 同步 local_path 到 by_province（merge 以 by_province 优先）
    by = ROOT / "data" / "clean" / "by_province"
    by_index = {}
    for p in by.glob("*-source.csv"):
        for s in sources:
            by_index[s["source_id"]] = s
    for p in by.glob("*-source.csv"):
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        header = list(rows[0].keys())
        header = [h for h in header if h is not None]
        n = 0
        clean_rows = []
        for r in rows:
            if not any(r.values()):
                continue
            row = {h: r.get(h) or "" for h in header}
            sid = row.get("source_id")
            if sid in by_index and not row.get("local_path") and by_index[sid].get("local_path"):
                row["local_path"] = by_index[sid]["local_path"]
                n += 1
            clean_rows.append(row)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
            w.writeheader()
            w.writerows(clean_rows)
        print(p.name, "local_path sync", n)


if __name__ == "__main__":
    main()
