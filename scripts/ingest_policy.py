"""政策层入库：data/stage/{批次}-policy.jsonl -> raw 全文存档 + clean CSV。

设计意图：采集阶段只产出宽松 JSONL，本脚本负责规范化、全文存档、哈希、
ID 分配与 by_province CSV 落表。大规模采集时每个批次一条命令即可。

**并行采集契约（重要）**：
  子智能体只写自己批次的 JSONL，**不写 CSV、不分配 ID、不碰 data/clean**。
  ID 由本脚本串行分配，因此多个 agent 并发产出 JSONL 不会撞主键。
  建议 agent 直接省略 policy_id / event_id 字段，交给脚本编号。

JSONL 每条记录字段见 docs/07-政策层.md §6；必填见 docs/02-数据字典.md §4。
额外的三个非表字段：
  full_text  str   正文 Markdown（写入 raw/原文.md）
  slug       str   目录名片段，缺省由 title 生成
  areas      list  [{area_id, entity_type, rel}]        -> area_policy_map
  events     list  [{entity_type, event_type, ymd, note, source_id}]  -> event

去重：同一 url 或同一 (doc_no, issuer) 已在库中则跳过，供多 agent 重复命中时兜底。

用法：
  python scripts/ingest_policy.py data/stage/POL-SD-01-policy.jsonl
  python scripts/ingest_policy.py --dry-run data/stage/xxx.jsonl
  python scripts/ingest_policy.py --group ZJ01 data/stage/xxx.jsonl   # 分散到 ZJ01-policy.csv
  python scripts/ingest_policy.py --purge POL-SD-01-policy            # 回滚该批次
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"
RAW = ROOT / "data" / "raw"

PROV_ABBR = {
    "110000": "BJ", "120000": "TJ", "130000": "HE", "140000": "SX", "150000": "NM",
    "210000": "LN", "220000": "JL", "230000": "HL", "310000": "SH", "320000": "JS",
    "330000": "ZJ", "340000": "AH", "350000": "FJ", "360000": "JX", "370000": "SD",
    "410000": "HA", "420000": "HB", "430000": "HN", "440000": "GD", "450000": "GX",
    "460000": "HI", "500000": "CQ", "510000": "SC", "520000": "GZ", "530000": "YN",
    "540000": "XZ", "610000": "SN", "620000": "GS", "630000": "QH", "640000": "NX",
    "650000": "XJ",
}

POLICY_COLS = [
    "policy_id", "title", "doc_no", "issuer", "issuer_level",
    "issued_ymd", "published_ymd", "date_precision", "doc_type",
    "source_kind", "province_code", "city_code", "county_code",
    "instruments", "scope_desc", "target_areas", "budget_wan",
    "valid_state", "url", "local_path", "hash_sha256", "full_text_chars",
    "summary", "credibility", "fetched_at", "record_state",
    "created_at", "updated_at", "created_by",
]
# docs/07 §3.1：source_kind 是封闭枚举（决策日志 2026-10），取值直接决定 credibility 口径。
SOURCE_KIND_VALUES = ("政策文件", "政府公报", "部门动态", "新闻发布")
# 只收已实际出现过的同义写法。认不出的值必须报错而不是猜一个——
# 把「部门动态」硬归成「政策文件」会造出 A 级假证据。
SOURCE_KIND_SYNONYMS = {"部门公开": "部门动态"}

MAP_COLS = ["area_id", "policy_id", "entity_type", "rel"]
EVENT_COLS = [
    "event_id", "area_id", "entity_type", "event_type", "ymd",
    "note", "source_id", "policy_id",
]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write_csv(path: Path, cols: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") or "" for c in cols})


def _slug(title: str, fallback: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", title).strip("-")
    s = s[:40] if s else fallback
    return s or "untitled"


def _cn_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5]", text))


def _next_id(prefix: str, existing: set[str]) -> str:
    n = 1
    while f"{prefix}{n:04d}" in existing:
        n += 1
    return f"{prefix}{n:04d}"


def _precision(r: dict) -> str:
    for f in ("issued_ymd", "published_ymd"):
        v = (r.get(f) or "").strip()
        if not v:
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return "day"
        if re.fullmatch(r"\d{4}-\d{2}", v):
            return "month"
        if re.fullmatch(r"\d{4}", v):
            return "year"
    return "unknown"


def purge_batch(batch: str) -> int:
    """移除某批次写入的 policy / area_policy_map / event 行，供修正后重灌。

    只清 CSV 行，不删 raw 存档（重灌会原地覆盖同一目录）。
    """
    targets: set[str] = set()
    for p in sorted(BY_PROV.glob("*-policy.csv")) + [CLEAN / "policy.csv"]:
        header, rows = _read_csv(p)
        if not header:
            continue
        keep, drop = [], []
        for r in rows:
            (drop if r.get("created_by") == batch else keep).append(r)
        for r in drop:
            if r.get("policy_id"):
                targets.add(r["policy_id"])
        if drop:
            _write_csv(p, header, keep)
            print(f"  - {p.name}: 删 {len(drop)} 行")

    if not targets:
        print(f"批次 {batch}: 无匹配 policy 行")
        return 0

    for p in sorted(BY_PROV.glob("*-area_policy_map.csv")) + [CLEAN / "area_policy_map.csv"]:
        header, rows = _read_csv(p)
        if not header:
            continue
        keep = [r for r in rows if r.get("policy_id") not in targets]
        if len(keep) != len(rows):
            _write_csv(p, header, keep)
            print(f"  - {p.name}: 删 {len(rows) - len(keep)} 行")

    for p in sorted(BY_PROV.glob("*-event.csv")) + [CLEAN / "event.csv"]:
        header, rows = _read_csv(p)
        if not header:
            continue
        keep = [r for r in rows if r.get("policy_id") not in targets]
        if len(keep) != len(rows):
            _write_csv(p, header, keep)
            print(f"  - {p.name}: 删 {len(rows) - len(keep)} 行")

    print(f"OK: 批次 {batch} 清理完成（policy {sorted(targets)}）")
    return 0


def ingest(path: Path, dry_run: bool = False, group: str = "") -> int:
    if not path.exists():
        print(f"找不到 {path}")
        return 1
    batch = path.stem
    # 并行采集时多个 agent 可能同省同时落表：用 group 分散到不同 CSV 文件，
    # 如 --group ZJ01 -> by_province/ZJ01-policy.csv
    file_group = group.strip() or None
    records = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"[{path.name}:{i}] JSON 解析失败: {e}")
            return 1

    # 现有集合：master 可能落后于 by_province（尚未 merge），两边都读
    _, pol_rows = _read_csv(CLEAN / "policy.csv")
    existing_pol = list(pol_rows)
    for p in sorted(BY_PROV.glob("*-policy.csv")):
        existing_pol.extend(_read_csv(p)[1])
    pol_ids = {r.get("policy_id") for r in existing_pol if r.get("policy_id")}
    existing_urls = {(r.get("url") or "").strip() for r in existing_pol if r.get("url")}
    existing_docs = {
        ((r.get("doc_no") or "").strip(), (r.get("issuer") or "").strip())
        for r in existing_pol
        if (r.get("doc_no") or "").strip()
    }
    # 同一内容常挂多个栏目 URL（不同 url 但同标题），仅按 url 去重会漏
    def _title_key(title: str, county: str) -> tuple[str, str]:
        t = re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-]+", "", title or "")
        return (t, county or "")

    existing_titles = {
        _title_key(r.get("title") or "", r.get("county_code") or "")
        for r in existing_pol
        if (r.get("title") or "").strip()
    }
    _, ev_rows = _read_csv(CLEAN / "event.csv")
    ev_ids = {r.get("event_id") for r in ev_rows if r.get("event_id")}
    map_existing: dict[str, set[tuple]] = {}
    for p in BY_PROV.glob("*-area_policy_map.csv"):
        for r in _read_csv(p)[1]:
            map_existing.setdefault(p.name.split("-")[0], set()).add(
                (r.get("area_id"), r.get("policy_id"))
            )

    today = date.today().isoformat()
    added_pol: list[tuple[str, dict]] = []
    added_map: list[tuple[str, dict]] = []
    added_ev: list[tuple[str, dict]] = []
    skipped_ev: list[tuple[str, str, str]] = []
    archives: list[tuple[Path, str, dict]] = []

    for r in records:
        prov = (r.get("province_code") or "").strip()
        abbr = PROV_ABBR.get(prov)
        if not abbr:
            print(f"跳过：province_code={prov!r} 无法映射省码缩写（{r.get('title')}）")
            return 1

        full_text = r.get("full_text") or ""
        if not full_text.strip():
            print(f"跳过：{r.get('title')} 缺 full_text（政策层必须存全文）")
            return 1

        # 去重：同一份文件可能被多个 agent/批次抓到（省级文件尤其常见）
        url_key = (r.get("url") or "").strip()
        doc_key = ((r.get("doc_no") or "").strip(), (r.get("issuer") or "").strip())
        if url_key and url_key in existing_urls:
            print(f"  跳过重复 url：{r.get('title')[:40]}")
            continue
        if doc_key[0] and doc_key in existing_docs:
            print(f"  跳过重复文号：{doc_key[0]} {r.get('title')[:30]}")
            continue
        tkey = _title_key(r.get("title") or "", (r.get("county_code") or ""))
        if tkey[0] and tkey in existing_titles:
            print(f"  跳过重复标题：{r.get('title')[:40]}")
            continue

        sk_raw = (r.get("source_kind") or "").strip()
        sk = SOURCE_KIND_SYNONYMS.get(sk_raw, sk_raw)
        if sk != sk_raw:
            print(f"  ~ source_kind「{sk_raw}」→「{sk}」  {(r.get('title') or '')[:30]}")
        if sk not in SOURCE_KIND_VALUES:
            print(f"跳过：source_kind={sk_raw!r} 不在 docs/07 §3.1 枚举内（{r.get('title')}）")
            return 1

        pid = (r.get("policy_id") or "").strip()
        if not pid or pid in pol_ids:
            pid = _next_id(f"P{prov[:2]}", pol_ids)
        pol_ids.add(pid)
        if url_key:
            existing_urls.add(url_key)
        if doc_key[0]:
            existing_docs.add(doc_key)
        existing_titles.add(tkey)

        slug = r.get("slug") or _slug(r.get("title") or "", pid)
        datestr = (r.get("published_ymd") or r.get("issued_ymd") or today).replace("-", "")
        rel_dir = Path(abbr) / f"{datestr}-{slug}"
        # 存档内容与哈希、字数同源：写入换行固定 LF，保证磁盘字节可复核
        body = f"# {r.get('title')}\n\n{full_text.strip()}\n"
        body_bytes = body.encode("utf-8")
        sha = hashlib.sha256(body_bytes).hexdigest()
        cn = _cn_chars(body)

        row = {c: "" for c in POLICY_COLS}
        for c in POLICY_COLS:
            if c in r and r[c] is not None:
                row[c] = str(r[c])
        # row 是从 r 原样搬过来的，这里覆盖为已规整、已通过枚举校验的取值
        row["source_kind"] = sk
        row.update({
            "policy_id": pid,
            "date_precision": r.get("date_precision") or _precision(r),
            "local_path": f"data/raw/{rel_dir.as_posix()}/原文.md",
            "hash_sha256": sha,
            "full_text_chars": str(cn),
            "fetched_at": r.get("fetched_at") or today,
            "valid_state": (r.get("valid_state") or "").strip() or "未知",
            "record_state": r.get("record_state") or "active",
            "created_at": r.get("created_at") or today,
            "updated_at": r.get("updated_at") or today,
            "created_by": r.get("created_by") or batch,
        })
        grp = file_group or abbr
        added_pol.append((grp, row))

        meta = {
            "policy_id": pid,
            "url": row["url"],
            "title": row["title"],
            "doc_no": row["doc_no"],
            "issuer": row["issuer"],
            "issuer_level": row["issuer_level"],
            "issued_ymd": row["issued_ymd"],
            "published_ymd": row["published_ymd"],
            "doc_type": row["doc_type"],
            "source_kind": row["source_kind"],
            "instruments": row["instruments"],
            "full_text_chars": row["full_text_chars"],
            "hash_sha256": sha,
            "fetched_at": row["fetched_at"],
            "batch": batch,
        }
        archives.append((RAW / rel_dir, body, meta))

        seen = map_existing.setdefault(grp, set())
        for a in r.get("areas") or []:
            key = (a.get("area_id"), pid)
            if key in seen:
                continue
            seen.add(key)
            added_map.append((grp, {
                "area_id": a.get("area_id") or "",
                "policy_id": pid,
                "entity_type": a.get("entity_type") or "area",
                "rel": a.get("rel") or "support",
            }))

        for e in r.get("events") or []:
            # event 是实体生命周期事件，area_id 必填（docs/02 §5）。
            # 政策级的「目标设定/名单公布」这类聚合事件不属于任何单一实体，
            # 应留在 policy.scope_desc/summary 里，不落 event 表。
            e_area = (e.get("area_id") or "").strip()
            if not e_area:
                skipped_ev.append((pid, e.get("event_type") or "", (e.get("note") or "")[:40]))
                continue
            eid = (e.get("event_id") or "").strip()
            if not eid or eid in ev_ids:
                eid = _next_id(f"E{prov[:2]}", ev_ids)
            ev_ids.add(eid)
            added_ev.append((grp, {
                "event_id": eid,
                "area_id": e_area,
                "entity_type": e.get("entity_type") or "area",
                "event_type": e.get("event_type") or "",
                "ymd": e.get("ymd") or "",
                "note": e.get("note") or "",
                "source_id": e.get("source_id") or "",
                "policy_id": pid,
            }))

    print(f"批次 {batch}: policy {len(added_pol)} / map {len(added_map)} / event {len(added_ev)}")
    if skipped_ev:
        print(f"  !! 跳过 {len(skipped_ev)} 条缺 area_id 的事件（entity 未定，不入 event 表）:")
        for pid, etype, note in skipped_ev:
            print(f"     {pid} [{etype}] {note}")
    for abbr, row in added_pol:
        print(f"  {row['policy_id']}  {abbr}  {row['issuer_level']:8s} "
              f"{row['doc_type']:3s}  {row['full_text_chars']:>5s}字  {row['title'][:38]}")

    if dry_run:
        print("dry-run：未写盘")
        return 0

    for d, body, meta in archives:
        d.mkdir(parents=True, exist_ok=True)
        # newline="\n"：Windows 下默认会转 CRLF，导致存档字节与 hash_sha256 不符
        (d / "原文.md").write_text(body, encoding="utf-8", newline="\n")
        (d / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )

    for table, cols, rows in (
        ("policy", POLICY_COLS, added_pol),
        ("area_policy_map", MAP_COLS, added_map),
        ("event", EVENT_COLS, added_ev),
    ):
        groups: dict[str, list[dict]] = {}
        for a, row in rows:
            groups.setdefault(a, []).append(row)
        for a, new_rows in groups.items():
            p = BY_PROV / f"{a}-{table}.csv"
            header, old = _read_csv(p)
            use_cols = header or cols
            _write_csv(p, use_cols, old + new_rows)
            print(f"  + {p.name}: {len(old)} -> {len(old) + len(new_rows)}")

    print("OK. 接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    group = ""
    if "--group" in args:
        i = args.index("--group")
        if i + 1 >= len(args):
            print("用法: ingest_policy.py --group {前缀} {file.jsonl}")
            sys.exit(1)
        group = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if args and args[0] == "--purge":
        if len(args) < 2:
            print("用法: ingest_policy.py --purge {批次号}")
            sys.exit(1)
        sys.exit(purge_batch(args[1]))
    if not args:
        print(__doc__)
        sys.exit(1)
    sys.exit(ingest(Path(args[0]), dry_run=dry, group=group))
