"""
按「待核裁定表」逐条落地改动（幂等，先 --dry-run）。

背景：2026-11-18 接手审校发现 `HANDOVER.md` 的 P4「15 条只需抽证据即可升级」
前提不成立——227 条待核里只有 174 条是媒体单源，其余卡在名称/规模/实体认定。
故改为逐条裁定：读原文 → 判定 → 落地。裁定与证据见
`reports/qa/接手审校-2026-11-18.md` §三 C。

输入：`data/stage/candidates/pending-decisions-{date}.csv`
列：
  area_id, abbr, action, new_name, new_status, new_cover, new_scale, policy_id, new_rel, note
  - action: upgrade（status→运行中）| rename（改 name+name_norm）| rel（改映射 rel）| note（只追加判词）
  - new_status 留空时按 action 推定：upgrade/rename→运行中，rel/note→不动
  - note 会以「｜【P4裁定 YYYY-MM-DD】…」追加到 summary（已存在则不重复追加）

约束（违反即报错退出，不静默跳过）：
  - area 是实体表，只写 `data/clean/by_province/{ABBR}-area.csv`，不碰 master
  - rename 后 name_norm 必须同县内唯一（active）
  - 不删记录、不改 record_state；升级只改 status
  - rel 变更同样只写 by_province 的 area_policy_map

用法：
  python scripts/adjudicate_pending_areas.py --dry-run
  python scripts/adjudicate_pending_areas.py
  python scripts/adjudicate_pending_areas.py --csv data/stage/candidates/pending-decisions-2026-11-18.csv
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
CAND = ROOT / "data" / "stage" / "candidates"
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－]+")
MARK = "【P4裁定"


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
    args = sys.argv[1:]
    dry = "--dry-run" in args
    csv_path = (
        Path(args[args.index("--csv") + 1])
        if "--csv" in args
        else CAND / f"pending-decisions-{date.today().isoformat()}.csv"
    )
    if not csv_path.exists():
        print(f"找不到裁定表: {csv_path}")
        return 2
    _, decisions = _read(csv_path)
    today = date.today().isoformat()
    changed = 0

    # 按省缓存，避免同一省反复读写
    cache: dict[str, tuple[list[str], list[dict[str, str]]]] = {}

    def area_rows(abbr: str):
        if abbr not in cache:
            cache[abbr] = _read(BY_PROV / f"{abbr}-area.csv")
        return cache[abbr]

    def map_rows(abbr: str):
        key = f"map:{abbr}"
        if key not in cache:
            cache[key] = _read(BY_PROV / f"{abbr}-area_policy_map.csv")
        return cache[key]

    dirty: set[str] = set()

    for d in decisions:
        aid = (d.get("area_id") or "").strip()
        abbr = (d.get("abbr") or "").strip().upper()
        action = (d.get("action") or "").strip()
        if not aid or not abbr:
            print(f"  跳过不完整行: {d}")
            continue
        header, rows = area_rows(abbr)
        hit = [r for r in rows if r.get("area_id") == aid]
        if not hit:
            print(f"  !! {aid} 不在 {abbr}-area.csv，跳过")
            continue
        r = hit[0]

        if action == "rel":
            pid = (d.get("policy_id") or "").strip()
            new_rel = (d.get("new_rel") or "").strip()
            mh, mrows = map_rows(abbr)
            hits = [m for m in mrows if m.get("area_id") == aid and m.get("policy_id") == pid]
            if not hits:
                print(f"  !! {aid} 在 area_policy_map 无 {pid}，跳过 rel 变更")
            else:
                for m in hits:
                    if m.get("rel") == new_rel:
                        print(f"  = {aid} {pid} rel 已是 {new_rel}")
                        continue
                    print(f"  {aid} {pid} rel: {m.get('rel')} -> {new_rel}")
                    m["rel"] = new_rel
                    changed += 1
                dirty.add(f"map:{abbr}")

        # 名称
        new_name = (d.get("new_name") or "").strip()
        if new_name and r.get("name") != new_name:
            # 同县 active 内 name_norm 唯一
            nn = PUNCT.sub("", new_name)
            cc = r.get("county_code")
            clash = [
                x for x in rows
                if x.get("area_id") != aid
                and x.get("record_state") == "active"
                and x.get("county_code") == cc
                and PUNCT.sub("", x.get("name") or "") == nn
            ]
            if clash:
                print(f"  !! {aid} 改名 {new_name} 与 {[x['area_id'] for x in clash]} 同县重名，中止")
                return 1
            print(f"  {aid} name: {r.get('name')} -> {new_name}")
            r["name"] = new_name
            r["name_norm"] = nn
            changed += 1

        # 状态
        new_status = (d.get("new_status") or "").strip()
        if not new_status and action in ("upgrade", "rename"):
            new_status = "运行中"
        if new_status and r.get("status") != new_status:
            print(f"  {aid} status: {r.get('status')} -> {new_status}")
            r["status"] = new_status
            changed += 1

        # 覆盖描述 / 村数
        nc = (d.get("new_cover") or "").strip()
        if nc and r.get("cover_desc") != nc:
            r["cover_desc"] = nc
            changed += 1
            print(f"  {aid} cover_desc 更新")
        ns = (d.get("new_scale") or "").strip()
        if ns and r.get("scale_villages") != ns:
            if not ns.isdigit():
                print(f"  !! {aid} new_scale={ns!r} 非整数，中止")
                return 1
            r["scale_villages"] = ns
            changed += 1
            print(f"  {aid} scale_villages={ns}")

        # 跨县工程键（parent_area_key）：R10 要求跨县单元各县分建时共享同一键
        np = (d.get("new_parent") or "").strip()
        if np and r.get("parent_area_key") != np:
            r["parent_area_key"] = np
            changed += 1
            print(f"  {aid} parent_area_key -> {np}")

        # 判词
        note = (d.get("note") or "").strip()
        if note:
            marker = f"{MARK} {today}】"
            if marker in (r.get("summary") or ""):
                print(f"  = {aid} 已有判词，跳过")
            else:
                base = (r.get("summary") or "").rstrip("｜ ")
                r["summary"] = (base + "｜" + marker if base else marker) + note
                changed += 1
                print(f"  {aid} summary 追加判词")

        if r.get("status") == "运行中" or action == "rename":
            r["updated_at"] = f"{today}T00:00:00+08:00"
        dirty.add(abbr)

    if dry:
        print(f"\ndry-run：将改 {changed} 处，未写盘")
        return 0

    for key in dirty:
        if key.startswith("map:"):
            abbr = key.split(":", 1)[1]
            h, rows = cache[key]
            _write(BY_PROV / f"{abbr}-area_policy_map.csv", h, rows)
        else:
            h, rows = cache[key]
            _write(BY_PROV / f"{key}-area.csv", h, rows)
    print(f"\n已写盘，共改 {changed} 处；接 merge_by_province -> build_db -> validate_db -> health_report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
