# -*- coding: utf-8 -*-
"""按官方名改写片区名称（幂等，先 --dry-run）。

只改 `name` / `name_norm`，必要时把 `cover_desc` 开头的旧名替换掉；
不碰 `area_id`、不改来源、不删记录。冲突检查：同县已有同名时拒绝执行。

用法：
  python scripts/rename_area.py --id A330089 --name 环铜鉴湖生态旅居片区 --dry-run
  python scripts/rename_area.py --id A330089 --name 环铜鉴湖生态旅居片区 --fix-cover
跑完接 merge_by_province -> build_db -> validate_db。
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"


def read(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows) -> None:
    for r in rows:
        assert set(r) <= set(hdr), f"{p.name}: 字段超出表头 {set(r) - set(hdr)}"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def norm(name: str) -> str:
    import re
    return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+", "", name or "")


def strip_prefix(name_norm: str, prefix_pool: set[str]) -> str:
    """去掉名称开头的行政区名前缀（淳安县大下姜片区 → 大下姜片区）。"""
    out = name_norm
    for _ in range(3):
        hit = next((p for p in sorted(prefix_pool, key=len, reverse=True)
                    if p and out.startswith(p) and len(out) > len(p) + 2), None)
        if not hit:
            break
        out = out[len(hit):]
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True, help="新的官方名称")
    ap.add_argument("--fix-cover", action="store_true", help="cover_desc 开头的旧名一并替换")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    new_name = args.name.strip()
    new_norm = norm(new_name)
    # 用 region 名称做前缀池，规范 name_norm（与库内既有约定一致）
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{ROOT/'data/db/片区库.sqlite3'}?mode=ro", uri=True)
        pool = {norm(r[0]) for r in con.execute("select name from region")}
        pool |= {"浙江省", "杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市",
                 "金华市", "衢州市", "舟山市", "台州市", "丽水市"}
        new_norm = strip_prefix(new_norm, pool)
        con.close()
    except Exception:  # noqa: BLE001
        pass
    today = date.today().isoformat()

    # 冲突检查（同县同名）
    target = None
    for p in sorted(BP.glob("*-area.csv")):
        hdr, rows = read(p)
        for r in rows:
            if r.get("area_id") != args.id:
                continue
            target = (p, hdr, rows, r)
            county = r.get("county_code")
            for other in rows:
                if other.get("area_id") != args.id and norm(other.get("name", "")) == new_norm \
                        and other.get("county_code") == county:
                    print(f"冲突：同县已有「{other.get('name')}」({other.get('area_id')})，终止")
                    return 1
        if target:
            break

    if not target:
        print(f"找不到 {args.id}")
        return 1

    p, hdr, rows, r = target
    old = r.get("name", "")
    print(f"{args.id}: 「{old}」 -> 「{new_name}」")
    print(f"  name_norm: {r.get('name_norm')} -> {new_norm}")
    if args.fix_cover:
        cover = r.get("cover_desc", "") or ""
        head = norm(old)
        if cover.startswith(old):
            r["cover_desc"] = new_name + cover[len(old):]
            print(f"  cover_desc 前缀已替换：{r['cover_desc'][:60]}…")
        elif "，" in cover:
            seg, rest = cover.split("，", 1)
            if head and norm(seg) == head:
                r["cover_desc"] = new_name + "，" + rest
                print(f"  cover_desc 首段已替换：{r['cover_desc'][:60]}…")
            else:
                print("  cover_desc 首段与旧名不一致，未自动改")
        else:
            print("  cover_desc 无法自动替换，需人工确认")
    r["name"] = new_name
    r["name_norm"] = new_norm
    r["updated_at"] = today

    if args.dry_run:
        print("dry-run 未写盘")
        return 0
    write(p, hdr, rows)
    print("已写盘：", p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
