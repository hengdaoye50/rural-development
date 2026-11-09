"""列出零产出分片的规模，供派发排序。"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SH = ROOT / "data" / "stage" / "shards"
BATCH = ROOT / "data" / "stage" / "batches"

ZERO = (
    "AH02 CQ02 FJ02 FJ03 GD02 GD03 GD04 GS01 GS02 GX01 HA02 HE01 HI01 HL01 "
    "HN02 JL01 LN01 LN02 NM01 NX01 QH01 SH02 SX01 TJ01 TJ02 XJ01 XZ01 YN01"
).split()

rows = []
for s in ZERO:
    p = SH / f"{s}-counties.csv"
    recs = [r for r in csv.DictReader(p.open("r", encoding="utf-8-sig")) if any(r.values())]
    areas = sum(len((r.get("area_ids") or "").split(";")) for r in recs if (r.get("area_ids") or "").strip())
    batch = BATCH / f"POL-{s}-policy.jsonl"
    got = sum(1 for l in batch.open("r", encoding="utf-8") if l.strip()) if batch.exists() else 0
    rows.append((s, len(recs), areas, got))

rows.sort(key=lambda x: (-x[2], -x[1]))
print(f"{'分片':<6}{'县数':>5}{'片区数':>7}{'已有批次行':>10}")
for s, n, a, g in rows:
    print(f"{s:<6}{n:>5}{a:>7}{g:>10}")
print(f"\n合计：{len(rows)} 分片 / {sum(r[1] for r in rows)} 县 / {sum(r[2] for r in rows)} 片区")
