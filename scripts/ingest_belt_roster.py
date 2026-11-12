"""按「名单」批量补建象征性单元（belt 层），并挂到名单所属的政策上。

口径依据（CLAUDE.md 统计范围 + docs/01 E07）：
  「示范带 / 示范圈 / 走廊 / 样板带 / 精品线路」等**未实体化设立**的命名单元入 belt，
  不入 area。有指挥部、联合党委、分村名单等实体机制的才入 area（T03）。

输入：data/stage/candidates/belt-roster-{ABBR}.csv，列：
  name, belt_type, city_code, county_code, cover_desc, theme,
  announced_ymd, year_precision, issuer, summary, source_policy_id, rel

用法：
  python scripts/ingest_belt_roster.py HB --dry-run
  python scripts/ingest_belt_roster.py HB
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
CAND = ROOT / "data" / "stage" / "candidates"
PUNCT = re.compile(
    r"[\s\u3000（）()《》〈〉「」" + '""' + r"''【】\[\]、，,。.：:；;·—\-－]+"
)

BELT_TYPES = {"带", "圈", "廊", "片", "走廊", "环", "线", "其他"}
PRECISION = {"day", "month", "year", "unknown"}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    abbr = args[0].upper()

    src = CAND / f"belt-roster-{abbr}.csv"
    if not src.exists():
        print(f"找不到 {src.relative_to(ROOT)}")
        return 1
    _, roster = _read(src)
    print(f"{abbr} belt 名单 {len(roster)} 条")

    _, region_rows = _read(ROOT / "data" / "clean" / "region.csv")
    counties = {r["region_code"] for r in region_rows if r.get("level") == "county"}
    _, policy_rows = _read(ROOT / "data" / "clean" / "policy.csv")
    policies = {r["policy_id"]: r for r in policy_rows if r.get("policy_id")}

    belt_p, belt_rows = _read(BY_PROV / f"{abbr}-belt.csv")
    src_p, src_rows = _read(BY_PROV / f"{abbr}-source.csv")
    if not belt_p:
        print(f"缺 {abbr}-belt.csv")
        return 1

    prov2 = next((r["province_code"][:2] for r in belt_rows if r.get("province_code")), "") \
        or {"LN": "21", "HE": "13", "HB": "42", "SD": "37", "ZJ": "33", "JS": "32"}.get(abbr, "")
    existing = {r.get("belt_id") for r in belt_rows}
    seq = max(
        (int(i[3:]) for i in existing if i and i.startswith(f"B{prov2}") and i[3:].isdigit()),
        default=0,
    )
    have_names = {PUNCT.sub("", r.get("name") or "") for r in belt_rows}

    # 从名单政策派生 source
    s_seq = max(
        (int(r["source_id"][3:]) for r in src_rows
         if r.get("source_id", "").startswith(f"S{prov2}") and r["source_id"][3:].isdigit()),
        default=0,
    )
    src_by_url = {r.get("url"): r.get("source_id") for r in src_rows if r.get("url")}
    policy_src: dict[str, str] = {}
    for pid in {r.get("source_policy_id", "").strip() for r in roster}:
        pr = policies.get(pid) if pid else None
        if not pr:
            continue
        if pr["url"] in src_by_url:
            policy_src[pid] = src_by_url[pr["url"]]
            continue
        s_seq += 1
        sid = f"S{prov2}{s_seq:04d}"
        src_rows.append({
            "source_id": sid, "area_id": "",
            "url": pr["url"], "title": pr["title"], "publisher": pr.get("issuer") or "",
            "published_ymd": pr.get("published_ymd") or "",
            "excerpt": f"{pr['title']}（按名单逐条补建象征性单元，共 {len(roster)} 条）",
            "fetched_at": date.today().isoformat(),
            "credibility": pr.get("credibility") or "A",
            "local_path": pr.get("local_path") or "",
            "hash_sha256": pr.get("hash_sha256") or "",
        })
        src_by_url[pr["url"]] = sid
        policy_src[pid] = sid
        print(f"  派生来源 {sid} <- {pid}")

    today = date.today().isoformat()
    errors, added, skipped = [], [], []
    for i, r in enumerate(roster, 1):
        name = (r.get("name") or "").strip()
        bt = (r.get("belt_type") or "带").strip()
        cc = (r.get("county_code") or "").strip()
        yp = (r.get("year_precision") or "unknown").strip()
        pid = (r.get("source_policy_id") or "").strip()
        if not name or bt not in BELT_TYPES or yp not in PRECISION:
            errors.append(f"第 {i} 行字段非法：name={name!r} belt_type={bt!r} precision={yp!r}")
            continue
        if cc not in counties:
            errors.append(f"第 {i} 行 county_code={cc} 不在 region 表")
            continue
        if pid and pid not in policies:
            errors.append(f"第 {i} 行 source_policy_id={pid} 不在 policy 表")
            continue
        if PUNCT.sub("", name) in have_names:
            skipped.append(name)
            continue

        seq += 1
        bid = f"B{prov2}{seq:04d}"
        sid = policy_src.get(pid, "")
        for sr in src_rows:
            if sr["source_id"] == sid and not sr.get("area_id"):
                sr["area_id"] = bid
        belt_rows.append({
            "belt_id": bid,
            "name": name,
            "name_norm": PUNCT.sub("", name),
            "belt_type": bt,
            "theme": r.get("theme", ""),
            "province_code": cc[:2] + "0000",
            "city_code": (r.get("city_code") or "").strip() or cc[:4] + "00",
            "county_code": cc,
            "cover_desc": (r.get("cover_desc") or "").strip() or name,
            "scale_villages": r.get("scale_villages", ""),
            "scale_towns": r.get("scale_towns", ""),
            "announced_ymd": (r.get("announced_ymd") or "").strip(),
            "year_precision": yp,
            "issuer": r.get("issuer", ""),
            "source_id": sid,
            "summary": r.get("summary", ""),
            "institutional_note": r.get("institutional_note", "") or "按省级名单补建，未见实体设立动作",
            "record_state": "active",
            "created_at": today,
            "updated_at": today,
            "created_by": f"roster-{abbr}",
        })
        have_names.add(PUNCT.sub("", name))
        added.append((bid, name, cc, pid))

    for sr in src_rows:
        if sr.get("area_id"):
            continue
        owner = next((r0["belt_id"] for r0 in belt_rows if r0.get("source_id") == sr["source_id"]), "")
        if owner:
            sr["area_id"] = owner

    for e in errors:
        print(f"  !! {e}")
    for a in added:
        print(f"  + {a[0]}  {a[1]}  ({a[2]}) <- {a[3]}")
    if skipped:
        print(f"  已存在跳过 {len(skipped)} 条")

    print(f"\n新增 {len(added)} / 跳过 {len(skipped)} / 错误 {len(errors)}")
    if errors:
        print("有错误，未写盘")
        return 1
    if dry:
        print("dry-run，未写盘")
        return 0

    _write(BY_PROV / f"{abbr}-belt.csv", belt_p, belt_rows)
    if src_rows:
        _write(BY_PROV / f"{abbr}-source.csv",
               src_p or ["source_id", "area_id", "url", "title", "publisher", "published_ymd",
                         "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256"],
               src_rows)
    print("已写入；接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
