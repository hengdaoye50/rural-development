"""按 `docs/02` 的 rel 语义清理政策链接真实性审计的结论。

输入（由 `scripts/audit_link_veracity.py` 产出）：
- `reports/qa/link-wrong.csv`：政策正文与片区完全无关 → 解除链接
- `reports/qa/link-weak.csv`：正文只出现县镇地名、未点名片区 → `rel` 降为 `mention`

只改 `area_policy_map`，不动 `area.status`——「片区是否够格入库」属 `docs/01` 准入问题，
不是 rel 语义问题，不在这里顺手改。

必须同时改 by_province 与 master：`merge_by_province.py` 对 map 表是「by_province 优先 +
master 补缺」语义，只删 by_province 里的行，master 的同一行会被当成补缺重新并回来。

    python scripts/apply_link_veracity_fix.py --dry-run
    python scripts/apply_link_veracity_fix.py
    python scripts/merge_by_province.py && python scripts/build_db.py && python scripts/validate_db.py
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"
WRONG = ROOT / "reports" / "qa" / "link-wrong.csv"
WEAK = ROOT / "reports" / "qa" / "link-weak.csv"
MAP_TABLE = "area_policy_map"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        return list(rdr.fieldnames or []), [r for r in rdr if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in header})


def _pairs(path: Path, need_col: str) -> dict[tuple[str, str], dict[str, str]]:
    header, rows = _read(path)
    if not header:
        print(f"找不到或为空：{path}")
        sys.exit(1)
    for col in ("area_id", "policy_id", need_col):
        if col not in header:
            print(f"{path} 缺列 {col}")
            sys.exit(1)
    return {(r["area_id"], r["policy_id"]): r for r in rows if r.get("area_id") and r.get("policy_id")}


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    wrong = _pairs(WRONG, "tier")
    weak = _pairs(WEAK, "tier")
    overlap = wrong.keys() & weak.keys()
    if overlap:
        print(f"warning：{len(overlap)} 条同时出现在两份清单里，按「解除」处理")

    prov_files = [BY_PROV / f"{p.name.split('-')[0]}-{MAP_TABLE}.csv"
                  for p in sorted(BY_PROV.glob(f"*-{MAP_TABLE}.csv"))]
    phases = [("by_province", prov_files), ("master", [CLEAN / f"{MAP_TABLE}.csv"])]

    stats: dict[str, tuple[Counter, Counter, int]] = {}
    total_touched = 0
    for label, targets in phases:
        removed: Counter = Counter()
        downgraded: Counter = Counter()
        already = 0
        touched = 0
        for path in targets:
            header, rows = _read(path)
            if not header:
                continue
            out: list[dict[str, str]] = []
            n_rm = n_dg = 0
            for r in rows:
                key = (r.get("area_id", ""), r.get("policy_id", ""))
                if key in wrong:
                    n_rm += 1
                    continue
                if key in weak:
                    if (r.get("rel") or "").strip() == "mention":
                        already += 1
                    else:
                        r = dict(r, rel="mention")
                        n_dg += 1
                out.append(r)
            if n_rm or n_dg:
                touched += 1
                prov = path.name.split("-")[0] if label == "by_province" else "master"
                removed[prov] += n_rm
                downgraded[prov] += n_dg
                if not dry:
                    _write(path, header, out)
            print(f"[{label}] {path.name:30s} {len(rows):5d} -> {len(out):5d}  (-{n_rm} / ~{n_dg})")
        stats[label] = (removed, downgraded, already)
        total_touched += touched

    print()
    for label, (removed, downgraded, already) in stats.items():
        print(f"{label}: 解除 {sum(removed.values())} 行 / 降 mention {sum(downgraded.values())} 行"
              f"（已降过的跳过 {already}）")
    removed, downgraded, _ = stats["by_province"]
    if removed:
        print("解除分布：" + "，".join(f"{k} {v}" for k, v in removed.most_common()))
    if downgraded:
        print("降级分布：" + "，".join(f"{k} {v}" for k, v in downgraded.most_common()))
    print(f"改动文件 {total_touched} 个" + ("（dry-run 未写盘）" if dry else ""))
    if not dry and total_touched:
        print("接着跑：merge_by_province.py -> build_db.py -> validate_db.py -> health_report.py")
    if not total_touched:
        print("两处均无待改行——已执行过或清单与库不一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
