"""打印新疆 A650001–A650005 的完整 tags 残留，供逐行重建（不做任何推断）。"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "data/clean/by_province/XJ-area.csv", encoding="utf-8-sig")))
for r in rows:
    if r["area_id"] in {"A650001", "A650002", "A650003", "A650004", "A650005"}:
        print("=" * 70)
        print(r["area_id"], r["name"])
        segs = r["tags"].split(",")
        for i, s in enumerate(segs):
            print(f"  tags[{i}] = {s!r}")
        print(f"  现状 town_codes={r['town_codes']!r} cover_desc={r['cover_desc']!r} "
              f"scale_villages={r['scale_villages']!r} scale_towns={r['scale_towns']!r}")
        print(f"  现状 issuer={r['issuer']!r} summary={r['summary']!r}")
