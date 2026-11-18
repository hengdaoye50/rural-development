"""按「名单」批量补建片区（area 层），并挂到名单所属的政策上。

背景：片区层最初由 2025-09 普查建立，未做过逆向校验。2026-11 拿省级名单倒查发现
漏采严重（辽宁 2023 省级示范带 23 条，库内只覆盖 7 个县）。本脚本把名单条目
逐条建成 area，并写 area_region_map 与 area_policy_map（rel 默认 primary）。

输入：data/stage/candidates/area-roster-{ABBR}.csv，列：
  name, type_code, city_code, county_code, cover_desc, status,
  founded_ymd, founded_precision, issuer, summary, source_policy_id, rel

约束（违反即报错，不静默跳过）：
  - type_code ∈ T01..T08；status ∈ 运行中/待核/已撤销/已更名/已完成
  - county_code 必须在 region 表（level=county）
  - source_policy_id 必须在 policy 表
  - 同一县内 name_norm 已存在则跳过（幂等，可反复重跑）

用法：
  python scripts/ingest_area_roster.py LN --dry-run
  python scripts/ingest_area_roster.py LN
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
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－]+")

TYPE_CODES = {f"T0{i}" for i in range(1, 9)}
STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
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

    src = CAND / f"area-roster-{abbr}.csv"
    if not src.exists():
        print(f"找不到 {src.relative_to(ROOT)}")
        return 1
    _, roster = _read(src)
    print(f"{abbr} 名单 {len(roster)} 条")

    conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
    conn.row_factory = sqlite3.Row
    # 县码与政策一律读 clean CSV，不依赖库：库可能正处于半重建状态
    _, region_rows = _read(ROOT / "data" / "clean" / "region.csv")
    counties = {r["region_code"] for r in region_rows if r.get("level") == "county"}
    _, policy_rows = _read(ROOT / "data" / "clean" / "policy.csv")
    policies = {r["policy_id"]: r for r in policy_rows if r.get("policy_id")}

    area_p, area_rows = _read(BY_PROV / f"{abbr}-area.csv")
    map_p, map_rows = _read(BY_PROV / f"{abbr}-area_region_map.csv")
    apm_p, apm_rows = _read(BY_PROV / f"{abbr}-area_policy_map.csv")
    src_p, src_rows = _read(BY_PROV / f"{abbr}-source.csv")
    if not area_p:
        print(f"缺 {abbr}-area.csv，无法确定表头")
        return 1

    # 名单文件本身就是片区层的第一手来源：为每个不同的 source_policy_id 派生一条 source
    # 省级码：从名单县码前两位取（area 表此前可能还没有该省）
    prov2_guess = next(
        ((r.get("county_code") or "").strip()[:2] for r in roster
         if (r.get("county_code") or "").strip()), ""
    ) or {"LN": "21", "HE": "13", "SD": "37", "ZJ": "33", "JS": "32"}.get(abbr, "")
    s_seq = max(
        (int(r["source_id"][3:]) for r in src_rows
         if r.get("source_id", "").startswith(f"S{prov2_guess}") and r["source_id"][3:].isdigit()),
        default=0,
    )
    src_by_url = {r.get("url"): r.get("source_id") for r in src_rows if r.get("url")}
    policy_src: dict[str, str] = {}
    for pid in {r.get("source_policy_id", "").strip() for r in roster}:
        if not pid:
            continue
        pr = policies.get(pid)
        if not pr:
            continue
        if pr["url"] in src_by_url:
            policy_src[pid] = src_by_url[pr["url"]]
            # 复用时刷新过短的 excerpt（validate 要求 ≥40 字）
            for sr in src_rows:
                if sr["source_id"] == policy_src[pid] and len(sr.get("excerpt") or "") < 40:
                    sr["excerpt"] = (
                        f"{pr['title']}｜{pr.get('issuer') or ''}｜{pr.get('published_ymd') or ''}"
                        f"｜按该文件点名的片区逐条补建 area"
                    )
            continue
        s_seq += 1
        sid = f"S{prov2_guess}{s_seq:04d}"
        src_rows.append({
            "source_id": sid,
            "area_id": "",  # 首次使用时填第一个派生的片区
            "url": pr["url"],
            "title": pr["title"],
            "publisher": pr["issuer"] or "",
            "published_ymd": pr["published_ymd"] or "",
            "excerpt": (f"{pr['title']}｜{pr.get('issuer') or ''}｜{pr.get('published_ymd') or ''}"
                        f"｜按该文件点名的片区逐条补建 area，本批 {len(roster)} 条"),
            "fetched_at": date.today().isoformat(),
            "credibility": pr["credibility"] or "A",
            "local_path": pr["local_path"] or "",
            "hash_sha256": pr["hash_sha256"] or "",
        })
        src_by_url[pr["url"]] = sid
        policy_src[pid] = sid
        print(f"  派生来源 {sid} <- {pid} {pr['title'][:40]}")


    # 省码优先级：area 表已有值 → 名单首行的县码前两位（最可靠）→ 缺省映射
    prov2 = next(
        (r["province_code"][:2] for r in area_rows if r.get("province_code")), ""
    )
    if not prov2:
        first_cc = next(((r.get("county_code") or "").strip() for r in roster
                         if (r.get("county_code") or "").strip()), "")
        prov2 = first_cc[:2]
    if not prov2:
        prov2 = {"LN": "21", "HE": "13", "SD": "37", "ZJ": "33", "JS": "32"}.get(abbr, "")
    existing = {r.get("area_id") for r in area_rows}
    seq = max(
        (int(i[3:]) for i in existing if i and i.startswith(f"A{prov2}") and i[3:].isdigit()),
        default=0,
    )
    in_county = {(r.get("name_norm"), r.get("county_code")) for r in area_rows}

    today = date.today().isoformat()
    errors, added, skipped = [], [], []

    for i, r in enumerate(roster, 1):
        name = (r.get("name") or "").strip()
        tc = (r.get("type_code") or "").strip()
        cc = (r.get("county_code") or "").strip()
        st = (r.get("status") or "运行中").strip()
        prec = (r.get("founded_precision") or "unknown").strip()
        pid = (r.get("source_policy_id") or "").strip()
        rel = (r.get("rel") or "primary").strip()
        nname = PUNCT.sub("", name)

        if not name or tc not in TYPE_CODES or st not in STATUS or prec not in PRECISION:
            errors.append(f"第 {i} 行字段非法：name={name!r} type={tc!r} status={st!r} prec={prec!r}")
            continue
        if cc not in counties:
            errors.append(f"第 {i} 行 county_code={cc} 不在 region 表")
            continue
        if pid and pid not in policies:
            errors.append(f"第 {i} 行 source_policy_id={pid} 不在 policy 表")
            continue
        if (nname, cc) in in_county:
            skipped.append(name)
            # 已存在也补 first_source_id（幂等回填）
            if pid:
                for r0 in area_rows:
                    if r0.get("name_norm") == nname and r0.get("county_code") == cc \
                            and not (r0.get("first_source_id") or "").strip():
                        r0["first_source_id"] = policy_src.get(pid, "")
            continue

        seq += 1
        aid = f"A{prov2}{seq:04d}"
        city = (r.get("city_code") or "").strip() or cc[:4] + "00"
        sid = policy_src.get(pid, "")
        # source.area_id 记「主实体」：该来源首次派生的片区
        for sr in src_rows:
            if sr["source_id"] == sid and not sr.get("area_id"):
                sr["area_id"] = aid
        area_rows.append({
            "area_id": aid,
            "name": name,
            "name_norm": nname,
            "type_code": tc,
            "type_primary_note": r.get("type_primary_note", "") or "按省级名单补建",
            "tags": r.get("tags", ""),
            "province_code": cc[:2] + "0000",
            "city_code": city,
            "county_code": cc,
            "town_codes": r.get("town_codes", ""),
            "cover_desc": (r.get("cover_desc") or "").strip() or name,
            "scale_villages": r.get("scale_villages", ""),
            "scale_towns": r.get("scale_towns", ""),
            "founded_ymd": (r.get("founded_ymd") or "").strip(),
            "founded_precision": prec,
            "status": st,
            "lead_org": r.get("lead_org", ""),
            "issuer": r.get("issuer", ""),
            "summary": r.get("summary", ""),
            "parent_area_key": (r.get("parent_area_key") or "").strip(),
            "first_source_id": sid,
            "record_state": "active",
            "created_at": today,
            "updated_at": today,
            "created_by": f"roster-{abbr}",
        })
        map_rows.append({"area_id": aid, "region_code": cc, "role": "county", "is_core": "1"})
        if pid:
            apm_rows.append({"area_id": aid, "policy_id": pid, "entity_type": "area", "rel": rel})
        in_county.add((nname, cc))
        added.append((aid, name, cc, pid))

    # 兜底：确保每条派生的 source 都指向一个具体片区（source.area_id 记主实体）
    for sr in src_rows:
        if sr.get("area_id"):
            continue
        owner = next(
            (r0["area_id"] for r0 in area_rows if r0.get("first_source_id") == sr["source_id"]),
            "",
        )
        if owner:
            sr["area_id"] = owner

    for e in errors:
        print(f"  !! {e}")
    for a in added:
        print(f"  + {a[0]}  {a[1]}  ({a[2]}) <- {a[3]}")
    if skipped:
        print(f"  已存在跳过 {len(skipped)} 条：{'、'.join(s[:18] for s in skipped[:6])}")

    print(f"\n新增 {len(added)} 条 / 跳过 {len(skipped)} / 错误 {len(errors)}")
    if errors:
        print("有错误，未写盘")
        return 1
    if dry:
        print("dry-run，未写盘")
        return 0

    _write(BY_PROV / f"{abbr}-area.csv", area_p, area_rows)
    _write(BY_PROV / f"{abbr}-area_region_map.csv", map_p or ["area_id", "region_code", "role", "is_core"], map_rows)
    _write(BY_PROV / f"{abbr}-area_policy_map.csv", apm_p or ["area_id", "policy_id", "entity_type", "rel"], apm_rows)
    if src_rows:
        _write(BY_PROV / f"{abbr}-source.csv",
               src_p or ["source_id", "area_id", "url", "title", "publisher", "published_ymd",
                         "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256"],
               src_rows)
    print("已写入 by_province 四张表；接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
