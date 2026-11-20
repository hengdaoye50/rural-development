"""把「媒体名单建档」的待核片区升级为官方依据（primary）。

场景：`ingest_area_media_roster.py` 建了 area + source、status=待核；
后来拿到 `.gov.cn` 官方原文（如广东 130 条名单），需把它们升级为正常在册记录。

动作（只写 by_province，幂等）：
  1. `{ABBR}-area_policy_map.csv` 增加 (area_id, policy_id, primary)
  2. `{ABBR}-area.csv` 里 `created_by=media-roster-{ABBR}` 且 `status=待核` 的片区 status → 运行中
  3. `{ABBR}-area_source_map.csv` 的 rel 保持（来源不变）

��意：不改 `area.first_source_id`（媒体来源仍留作证据链），只加政策挂接与改状态。

用法：
  python scripts/upgrade_media_roster.py GD P440001 --dry-run
  python scripts/upgrade_media_roster.py GD P440001
  # 跑完接 merge_by_province -> build_db -> validate_db -> health_report -> check_doc_caliber
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"


def _read(p: Path):
    if not p.exists():
        return [], []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(p: Path, hdr: list[str], rows: list[dict[str, str]]) -> None:
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in hdr})


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) < 2:
        print(__doc__)
        return 2
    abbr, pid = args[0].upper(), args[1]
    creator = f"media-roster-{abbr}"

    ap, arows = _read(BY_PROV / f"{abbr}-area.csv")
    mp, mrows = _read(BY_PROV / f"{abbr}-area_policy_map.csv")
    have = {(r["area_id"], r["policy_id"]) for r in mrows}
    targets = [r for r in arows if r.get("created_by") == creator and r.get("status") == "待核"]
    if not targets:
        print(f"{abbr}: 没有 created_by={creator} 且 status=待核 的片区（可能已升级）")
        return 0
    add = [r for r in targets if (r["area_id"], pid) not in have]
    print(f"{abbr}: 目标 {len(targets)} 条；需新增 policy 挂接 {len(add)} 条")
    for r in targets[:5]:
        print(f"  {r['area_id']} {r['name'][:30]} 待核 -> 运行中")
    if dry:
        print("dry-run，未写盘")
        return 0

    for r in targets:
        r["status"] = "运行中"
        r["updated_at"] = r.get("updated_at") or ""
    for r in add:
        mrows.append({"area_id": r["area_id"], "policy_id": pid, "rel": "primary",
                      "note": f"{creator} 官方原文升级"})
    _write(BY_PROV / f"{abbr}-area.csv", ap, arows)
    _write(BY_PROV / f"{abbr}-area_policy_map.csv", mp, mrows)
    print(f"已写 {abbr}-area.csv 与 {abbr}-area_policy_map.csv")
    print("接着跑：merge_by_province -> build_db -> validate_db -> health_report -> check_doc_caliber")
    return 0


if __name__ == "__main__":
    sys.exit(main())
