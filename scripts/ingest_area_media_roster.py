"""按「媒体名单」批量建档（只有 source，没有 .gov.cn 政策全文）。

用途：省级名单常见于党报报道（C 级权威媒体），但拿不到 `.gov.cn` 全文。
按 `docs/01` §5，C 级媒体可单独作为来源；但本项目对「无官方全文」的记录统一记
`status=待核`（与 `mark_unbacked_areas.py` 口径一致），等官方原文出现后再升级。
因此本脚本**不写 `policy`、不写 `area_policy_map`**，只写：

  area（含 first_source_id）+ area_region_map + source + area_source_map

输入：`data/stage/candidates/area-media-roster-{ABBR}.csv`，列：
  name, type_code, city_code, county_code, cover_desc, status, founded_ymd,
  founded_precision, issuer, summary, source_url, source_title, publisher,
  published_ymd, credibility, excerpt, local_path[, seq]

约束（违反即报错）：
  - 每个 `source_url` 只建一条 `source`，其 `area_id` 记该来源首个片区（主实体）
  - `local_path` 必须存在（媒体也要留快照）；有文件则算 hash_sha256
  - `county_code` 必须在 region；允许直辖市/直筒子市用市级码并注 `cover_desc`
  - 同县同名（name_norm）已存在则跳过（幂等）
  - 只写 by_province，不碰 master

用法：
  python scripts/ingest_area_media_roster.py GD --dry-run
  python scripts/ingest_area_media_roster.py GD
"""
from __future__ import annotations

import csv
import hashlib
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
CAND = ROOT / "data" / "stage" / "candidates"
DB = ROOT / "data" / "db" / "片区库.sqlite3"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－]+")
TYPE_CODES = {f"T0{i}" for i in range(1, 9)}
PRECISION = {"day", "month", "year", "unknown"}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\r\n")
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
    src_csv = CAND / f"area-media-roster-{abbr}.csv"
    if "--csv" in sys.argv:      # 同省多份名单（省级批次 / 市级名单）时指定具体文件
        src_csv = Path(sys.argv[sys.argv.index("--csv") + 1])
        if not src_csv.is_absolute():
            src_csv = (ROOT / src_csv).resolve()
    if not src_csv.exists():
        print(f"找不到 {src_csv}")
        return 1
    _, items = _read(src_csv)
    today = date.today().isoformat()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    counties = {r["region_code"] for r in con.execute(
        "select region_code from region where level in ('county','city')")}

    ap, arows = _read(BY_PROV / f"{abbr}-area.csv")
    mp, mrows = _read(BY_PROV / f"{abbr}-area_region_map.csv")
    sp, srows = _read(BY_PROV / f"{abbr}-source.csv")
    xp, xrows = _read(BY_PROV / f"{abbr}-area_source_map.csv")
    have = {(r.get("county_code"), PUNCT.sub("", r.get("name") or "")) for r in arows}
    have_norm = {(r.get("county_code"), PUNCT.sub("", r.get("name_norm") or "")) for r in arows}
    seq_area = max([int(r["area_id"][3:]) for r in arows if r.get("area_id", "").startswith("A")] or [0])
    prov2 = (items[0].get("county_code", "")[:2] if items else "").strip()
    # source_id 两套历史编号：新版 S{省2}{4位}，早期省份是 S{3位}（浙江 S001…）。
    # 沿用本省已有风格，避免同省两套编号并存。
    legacy = [int(m.group(1)) for r in srows
              for m in [re.match(r"^S(\d{3,6})$", (r.get("source_id") or "").strip())] if m]
    pref = [int((r.get("source_id") or "")[4:]) for r in srows
            if (r.get("source_id") or "").startswith("S" + prov2)
            and (r.get("source_id") or "")[4:].isdigit()]
    use_legacy = bool(legacy) and not pref
    seq_src = max(legacy) if use_legacy else max(pref or [0])

    errors, adds, skipped = [], [], []
    src_by_url: dict[str, dict[str, str]] = {}
    for it in items:
        name = (it.get("name") or "").strip()
        cc = (it.get("county_code") or "").strip()
        tc = (it.get("type_code") or "T01").strip()
        status = (it.get("status") or "待核").strip()
        prec = (it.get("founded_precision") or "unknown").strip()
        url = (it.get("source_url") or "").strip()
        lp = (it.get("local_path") or "").strip()
        if not name or tc not in TYPE_CODES or prec not in PRECISION:
            errors.append(f"{name}: 字段非法"); continue
        if not cc or cc not in counties:
            errors.append(f"{name}: county_code={cc} 不在 region"); continue
        if not url:
            errors.append(f"{name}: 缺 source_url"); continue
        if not lp or not (ROOT / lp).exists():
            errors.append(f"{name}: local_path 不存在 {lp}"); continue
        prov2 = prov2 or cc[:2]
        nn = PUNCT.sub("", name)
        if (cc, nn) in have or (cc, nn) in have_norm:
            skipped.append(name); continue

        sid = src_by_url.get(url, {}).get("source_id")
        if not sid:
            seq_src += 1
            sid = f"S{seq_src:03d}" if use_legacy else f"S{prov2}{seq_src:04d}"
            src_by_url[url] = {
                "source_id": sid, "area_id": "", "url": url,
                "title": (it.get("source_title") or "").strip(),
                "publisher": (it.get("publisher") or "").strip(),
                "published_ymd": (it.get("published_ymd") or "").strip(),
                "excerpt": (it.get("excerpt") or "").strip(),
                "fetched_at": today + "T00:00:00+08:00",
                "credibility": (it.get("credibility") or "C").strip(),
                "local_path": lp,
                "hash_sha256": hashlib.sha256((ROOT / lp).read_bytes()).hexdigest(),
                "source_kind": "新闻",
            }
        seq_area += 1
        aid = f"A{prov2}{seq_area:04d}"
        if not src_by_url[url]["area_id"]:
            src_by_url[url]["area_id"] = aid
        adds.append((aid, it, cc, nn, sid))
        have.add((cc, nn))

    if errors:
        print("错误（未写盘）：")
        for e in errors[:20]:
            print("  -", e)
        return 1

    print(f"{abbr} 媒体名单 {len(items)} 条：新增 {len(adds)} / 跳过 {len(skipped)} / 错误 0")
    for aid, it, cc, nn, sid in adds[:8]:
        print(f"  + {aid} {it['name'][:34]} ({cc}) <- {sid}")
    if len(adds) > 8:
        print(f"  ... 共 {len(adds)} 条")
    if dry:
        print("dry-run，未写盘")
        return 0

    for aid, it, cc, nn, sid in adds:
        arows.append({
            "area_id": aid, "name": it["name"], "name_norm": nn,
            "type_code": it.get("type_code") or "T01",
            "type_primary_note": (it.get("type_primary_note") or "省级名单（媒体首发，待补官方原文）"),
            "tags": it.get("tags", ""), "province_code": cc[:2] + "0000",
            "city_code": it.get("city_code", ""), "county_code": cc,
            "town_codes": it.get("town_codes", ""),
            "cover_desc": it.get("cover_desc", ""), "scale_villages": it.get("scale_villages", ""),
            "scale_towns": it.get("scale_towns", ""), "founded_ymd": it.get("founded_ymd", ""),
            "founded_precision": it.get("founded_precision") or "unknown",
            "status": it.get("status") or "待核", "lead_org": it.get("lead_org", ""),
            "issuer": it.get("issuer", ""), "summary": it.get("summary", ""),
            "parent_area_key": it.get("parent_area_key", ""), "first_source_id": sid,
            "record_state": "active", "created_at": today, "updated_at": today,
            "created_by": f"media-roster-{abbr}",
        })
        mrows.append({"area_id": aid, "region_code": cc, "role": "county", "is_core": "1"})
        xrows.append({"area_id": aid, "source_id": sid, "entity_type": "area", "rel": "primary"})

    for s in src_by_url.values():
        srows.append(s)

    _write(BY_PROV / f"{abbr}-area.csv", ap or list(arows[0].keys()), arows)
    _write(BY_PROV / f"{abbr}-area_region_map.csv", mp or ["area_id", "region_code", "role", "is_core"], mrows)
    _write(BY_PROV / f"{abbr}-source.csv", sp or list(srows[0].keys()), srows)
    _write(BY_PROV / f"{abbr}-area_source_map.csv", xp or ["area_id", "source_id", "entity_type", "rel"], xrows)
    print(f"已写 by_province 四张表（{len(adds)} 条 area / {len(src_by_url)} 条 source）")
    print("接着跑：merge_by_province -> build_db -> validate_db -> health_report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
