"""把 reports/qa/missing-policy-links-review.md 里判定为 primary/support 的行写成 area_policy_map 映射。

只写 data/clean/by_province/{ABBR}-area_policy_map.csv，不碰根表与 sqlite。
mention 不挂：rel=mention 只是「正文提到」，不构成政策依据，挂上会虚增覆盖率。
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BY_PROV = ROOT / "data" / "clean" / "by_province"
REVIEW = ROOT / "reports" / "qa" / "missing-policy-links-review.md"
WANT = {"primary", "support"}
COLS = ["area_id", "policy_id", "entity_type", "rel"]


def _read(path: Path):
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def parse_review() -> list[tuple[str, str, str]]:
    out = []
    for line in REVIEW.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not re.fullmatch(r"A\d{6}", cells[0]):
            continue
        area, _name, policy, verdict = cells[0], cells[1], cells[2], cells[3]
        if verdict in WANT and re.fullmatch(r"P\d{6}", policy):
            out.append((area, policy, verdict))
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    pairs = parse_review()
    print(f"待挂接 {len(pairs)} 条（primary/support）")

    conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
    prov_of_policy = dict(conn.execute("SELECT policy_id, province_code FROM policy"))
    abbr = {
        "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
        "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
        "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
        "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
        "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
        "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
        "650000": "XJ",
    }

    cache: dict[str, tuple[list[str], list[dict]]] = {}
    added = skipped = 0
    for area_id, policy_id, rel in pairs:
        prov = prov_of_policy.get(policy_id)
        if not prov or prov not in abbr:
            print(f"  !! 跳过 {area_id}<-{policy_id}: 省份未知")
            skipped += 1
            continue
        ab = abbr[prov]
        path = BY_PROV / f"{ab}-area_policy_map.csv"
        header, rows = cache.get(ab, ([], []))
        if not header and ab not in cache:
            header, rows = _read(path)
            header = header or COLS
            cache[ab] = (header, rows)
        header, rows = cache[ab]
        if any(r.get("area_id") == area_id and r.get("policy_id") == policy_id for r in rows):
            skipped += 1
            continue
        rows.append({"area_id": area_id, "policy_id": policy_id, "entity_type": "area", "rel": rel})
        added += 1

    for ab, (header, rows) in cache.items():
        if not dry:
            _write(BY_PROV / f"{ab}-area_policy_map.csv", header, rows)
    print(f"写入 {added} 条 / 跳过 {skipped} 条 -> {len(cache)} 个省级文件")
    if not dry:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    else:
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
