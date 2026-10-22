"""更精确地把 raw 快照挂到 source.local_path（优先 URL）。"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"


def main() -> None:
    snaps = []
    for meta in RAW.rglob("meta.json"):
        folder = meta.parent
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            continue
        body = ""
        for tf in list(folder.glob("*.md")) + list(folder.glob("*.txt")):
            body += tf.read_text(encoding="utf-8", errors="ignore")
        snaps.append(
            {
                "url": (m.get("url") or "").strip(),
                "title": (m.get("title") or folder.name).strip(),
                "path": str(folder.relative_to(ROOT)).replace("\\", "/"),
                "body": body,
            }
        )

    path = CLEAN / "source.csv"
    sources = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    header = list(sources[0].keys())
    changed = 0
    for s in sources:
        if s.get("local_path"):
            continue
        url = (s.get("url") or "").strip().rstrip("/")
        title = (s.get("title") or "").strip()
        hit = None
        for snap in snaps:
            if url and snap["url"] and (
                url == snap["url"].rstrip("/") or url[:40] == snap["url"].rstrip("/")[:40]
            ):
                hit = snap
                break
        if not hit and title:
            for snap in snaps:
                if title[:15] and title[:15] in snap["title"]:
                    hit = snap
                    break
                if title[:15] and title[:15] in snap["body"]:
                    hit = snap
                    break
        if hit:
            s["local_path"] = hit["path"]
            changed += 1
            print("link", s["source_id"], "->", hit["path"])

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(sources)
    print("linked", changed, "/", len(sources))


if __name__ == "__main__":
    main()
