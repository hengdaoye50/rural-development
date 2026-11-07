import csv
import json
from pathlib import Path

ROOT = Path(".")
CLEAN = ROOT / "data" / "clean"
RAW = ROOT / "data" / "raw"

sources = list(csv.DictReader((CLEAN / "source.csv").open(encoding="utf-8-sig", newline="")))
snaps = []
for meta in RAW.rglob("meta.json"):
    folder = meta.parent
    try:
        m = json.loads(meta.read_text(encoding="utf-8"))
    except Exception as e:
        print("bad meta", meta, e)
        continue
    body = ""
    for tf in folder.glob("*.md"):
        body += tf.read_text(encoding="utf-8", errors="ignore")
    snaps.append(
        {
            "url": m.get("url") or "",
            "title": m.get("title") or folder.name,
            "path": str(folder.relative_to(ROOT)).replace("\\", "/"),
            "body": body,
            "folder": folder.name,
        }
    )

print("snapshots", len(snaps))
for s in snaps:
    print(" SNAP", s["folder"], "|", s["title"][:50], "|", s["url"][:60])

print("\n--- sources without local_path ---")
for s in sources:
    if s.get("local_path"):
        continue
    print(s["source_id"], "|", (s.get("title") or "")[:50], "|", (s.get("url") or "")[:50])
