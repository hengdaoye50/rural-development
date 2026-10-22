"""M2 数据回填：area_source_map、时间、local_path 快照。"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY = CLEAN / "by_province"
STAGE = ROOT / "data" / "stage"
RAW = ROOT / "data" / "raw"


def _read(p: Path) -> list[dict[str, str]]:
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write(p: Path, rows: list[dict[str, str]], header: list[str]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in header})


def build_area_source_map() -> int:
    """由 first_source_id + source.area_id 生成多对多映射。"""
    areas = _read(CLEAN / "area.csv")
    belts = _read(CLEAN / "belt.csv")
    sources = _read(CLEAN / "source.csv")
    s_by_id = {s["source_id"]: s for s in sources}

    rows: dict[tuple[str, str], dict[str, str]] = {}
    for a in areas:
        aid = a["area_id"]
        sid = a.get("first_source_id") or ""
        if sid and sid in s_by_id:
            rows[(aid, sid)] = {
                "area_id": aid,
                "source_id": sid,
                "entity_type": "area",
                "rel": "primary",
            }
    for s in sources:
        ref = s.get("area_id") or ""
        sid = s["source_id"]
        if ref.startswith("A"):
            rows.setdefault(
                (ref, sid),
                {"area_id": ref, "source_id": sid, "entity_type": "area", "rel": "primary"},
            )
        elif ref.startswith("B"):
            rows[(ref, sid)] = {
                "area_id": ref,
                "source_id": sid,
                "entity_type": "belt",
                "rel": "primary",
            }
    for b in belts:
        sid = b.get("source_id") or ""
        if sid:
            rows[(b["belt_id"], sid)] = {
                "area_id": b["belt_id"],
                "source_id": sid,
                "entity_type": "belt",
                "rel": "primary",
            }

    header = ["area_id", "source_id", "entity_type", "rel"]
    out = list(rows.values())
    _write(CLEAN / "area_source_map.csv", out, header)
    print(f"area_source_map: {len(out)}")
    return len(out)


def backfill_times() -> int:
    """从 stage 候选回填 founded_ymd / precision。"""
    changed = 0
    stage_index: dict[str, dict[str, str]] = {}
    for p in STAGE.glob("*-candidates.csv"):
        for r in _read(p):
            name = (r.get("name") or "").strip()
            if name:
                stage_index[name] = r

    for prov_file in sorted(BY.glob("*-area.csv")):
        rows = _read(prov_file)
        header = list(rows[0].keys()) if rows else None
        if not header:
            continue
        local = 0
        for r in rows:
            name = (r.get("name") or "").strip()
            if r.get("founded_ymd") and r.get("founded_precision") not in ("", "unknown"):
                continue
            src = stage_index.get(name)
            if not src:
                continue
            ymd = (src.get("founded_ymd") or "").strip()
            if not ymd:
                continue
            r["founded_ymd"] = ymd
            if len(ymd) == 4:
                r["founded_precision"] = "year"
            elif len(ymd) == 7:
                r["founded_precision"] = "month"
            else:
                r["founded_precision"] = "day"
            if not r.get("lead_org") and src.get("lead_org"):
                r["lead_org"] = src["lead_org"]
            local += 1
            changed += 1
        if local:
            _write(prov_file, rows, header)
            print(f"{prov_file.name}: backfilled time {local}")
    return changed


def backfill_local_path() -> int:
    """把 data/raw 快照路径写回 source.local_path。"""
    changed = 0
    # 收集 raw 快照：meta.json / 原文.md
    snapshots: list[dict[str, str]] = []
    for meta in RAW.rglob("meta.json"):
        folder = meta.parent
        text_files = list(folder.glob("*.md")) + list(folder.glob("*.txt"))
        body = ""
        title = folder.name
        url = ""
        for tf in text_files:
            body += tf.read_text(encoding="utf-8", errors="ignore")[:2000]
        try:
            import json

            m = json.loads(meta.read_text(encoding="utf-8"))
            title = m.get("title") or title
            url = m.get("url") or ""
        except Exception:
            pass
        rel = str(folder.relative_to(ROOT)).replace("\\", "/")
        snapshots.append(
            {"title": title, "url": url, "path": rel, "body": body, "folder": folder.name}
        )

    sources = _read(CLEAN / "source.csv")
    header = list(sources[0].keys()) if sources else [
        "source_id", "area_id", "url", "title", "publisher", "published_ymd",
        "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256",
    ]
    for s in sources:
        if s.get("local_path"):
            continue
        url = s.get("url") or ""
        title = s.get("title") or ""
        hit = None
        for snap in snapshots:
            if url and snap["url"] and url == snap["url"]:
                hit = snap
                break
            if title and title[:12] in snap["title"]:
                hit = snap
                break
            if title and title[:10] in snap["body"]:
                hit = snap
                break
        if hit:
            s["local_path"] = hit["path"]
            changed += 1
    if changed:
        _write(CLEAN / "source.csv", sources, header)
    print(f"local_path filled: {changed}")
    return changed


def main() -> int:
    build_area_source_map()
    backfill_times()
    backfill_local_path()
    return 0


if __name__ == "__main__":
    sys.exit(main())
