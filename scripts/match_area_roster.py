"""名单文件 ↔ 库内片区 集合匹配。

用途：把一份官方名单（省/市/县公布的片区名录）里的片区名称，与库内片区
做匹配，输出「名单 → area_id」的对应表，供人工裁定后定点补依据。

名单 CSV 需要的列（缺列允许，按序识别）：
    county        县名，如「淳安县」「磐安县」
    area_name     名单原文的片区名称
    key_village   重点村/核心村（可选）
    source_url    名单出处 URL（可选）
    note          备注（可选）

用法：
    python scripts/match_area_roster.py data/stage/candidates/roster-zj-batch1.csv
    python scripts/match_area_roster.py roster.csv --out reports/qa/roster-match.csv
    python scripts/match_area_roster.py roster.csv --status 待核   # 只跟待核片区比
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "db" / "片区库.sqlite3"
AREA_CSV = ROOT / "data" / "clean" / "area.csv"

# 名称归一：去掉引号、间隔号、行政区划前缀，抹平「片区/组团/示范片」这类通名
QUOTE_CHARS = "\"'“”‘’「」『』《》·、,，（）()【】[] "
GENERIC_SUFFIXES = [
    "乡村振兴示范片区", "乡村振兴片区", "和美乡村片区", "示范片区", "片区",
    "组团片区", "共富片区", "精品片区", "示范片", "组团", "联合体", "集聚区", "示范带",
]


def _strip_county_prefix(s: str, county: str) -> str:
    """只在显式给了县名、且名字确实以该县名开头时剥离前缀。

    不能用 `^[\\u4e00-\\u9fa5]{2,4}(县|区|市)` 这种正则：它会把
    「海霞片区」整串吃掉（「海霞片」+「区」），使所有以「片区」结尾的名字
    归一成空串，进而任意两条都判为同名。这是本脚本踩过的坑。
    """
    c = (county or "").strip()
    if not c:
        return s
    for cand in (c, re.sub(r"(县|区|市|自治县|旗)$", "", c)):
        if cand and s.startswith(cand) and len(s) - len(cand) >= 2:
            return s[len(cand):]
    return s


def norm(name: str, county: str = "") -> str:
    s = (name or "").strip()
    for ch in QUOTE_CHARS:
        s = s.replace(ch, "")
    s = _strip_county_prefix(s, county)
    for suf in GENERIC_SUFFIXES:
        if s.endswith(suf) and len(s) > len(suf) + 1:
            s = s[: -len(suf)]
            break
    return s


def core_chars(name: str, county: str = "") -> set[str]:
    return set(norm(name, county))


def overlap(a: str, b: str, county: str = "") -> float:
    ca, cb = core_chars(a, county), core_chars(b, county)
    if not ca or not cb:
        return 0.0
    return len(ca & cb) / max(len(ca), len(cb))


def resolve_county(conn: sqlite3.Connection, county: str) -> list[tuple[str, str]]:
    """县名 -> [(code, name)]，只认 level=county。"""
    s = (county or "").strip()
    if not s:
        return []
    if s.isdigit() and len(s) == 6:
        rows = conn.execute(
            "select region_code, name from region where region_code = ?", (s,)
        ).fetchall()
        return rows
    # 精确名 或 去后缀名
    base = re.sub(r"(县|区|市|自治县|旗)$", "", s)
    rows = conn.execute(
        "select region_code, name from region where level='county' and (name = ? or short_name = ? or name like ?)",
        (s, s, f"%{base}%"),
    ).fetchall()
    # 优先完全匹配
    exact = [r for r in rows if r[1] == s]
    return exact or rows


def load_areas(status_filter: str | None) -> list[dict]:
    with io.open(AREA_CSV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if status_filter:
        rows = [r for r in rows if r.get("status") == status_filter]
    return rows


def read_roster(path: Path) -> list[dict]:
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rdr = csv.reader(f)
        rows = [r for r in rdr if any(c.strip() for c in r)]
    if not rows:
        return []
    head = [h.strip() for h in rows[0]]
    known = {"county", "area_name", "key_village", "source_url", "note", "province"}
    if known & set(head):
        out = []
        for r in rows[1:]:
            d = dict(zip(head, r))
            out.append({k: (v or "").strip() for k, v in d.items()})
        return out
    # 无表头：按 county, area_name, key_village, source_url, note 顺序
    out = []
    for r in rows:
        r = list(r) + [""] * (5 - len(r))
        out.append(
            {
                "county": r[0].strip(),
                "area_name": r[1].strip(),
                "key_village": r[2].strip(),
                "source_url": r[3].strip(),
                "note": r[4].strip(),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roster", type=Path, help="名单 CSV")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--status", default=None, help="只与该 status 的库内片区比，如 待核")
    ap.add_argument("--min-overlap", type=float, default=0.6)
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    conn = sqlite3.connect(DB)
    areas = load_areas(args.status)
    roster = read_roster(args.roster)
    print(f"名单 {len(roster)} 条 | 库内比较范围 {len(areas)} 条\n")

    by_county: dict[str, list[dict]] = {}
    for a in areas:
        by_county.setdefault(a["county_code"], []).append(a)

    results = []
    unmatched = []
    for r in roster:
        cname = r.get("county", "")
        aname = r.get("area_name", "")
        codes = resolve_county(conn, cname)
        if not codes:
            unmatched.append((cname, aname, "县名无法解析"))
            continue
        if len(codes) > 1:
            # 取名称完全相同的那个
            same = [c for c in codes if c[1] == cname]
            codes = same or codes[:1]
        ccode = codes[0][0]
        cn_name = codes[0][1]
        pool = by_county.get(ccode, [])
        # 也允许片区落在同市其他县（跨县片区），但单独标注
        best = None
        for a in pool:
            if norm(a["name"], cn_name) == norm(aname, cn_name):
                best = (a, "T1_同名", 1.0)
                break
            ov = overlap(a["name"], aname, cn_name)
            if best is None or ov > best[2]:
                best = (a, "T3_形近", ov)
        if best and (best[1] == "T1_同名" or best[2] >= args.min_overlap):
            results.append(
                {
                    "roster_county": cname,
                    "county_code": ccode,
                    "roster_area_name": aname,
                    "roster_key_village": r.get("key_village", ""),
                    "matched_area_id": best[0]["area_id"],
                    "area_name": best[0]["name"],
                    "area_status": best[0]["status"],
                    "match_tier": best[1],
                    "score": f"{best[2]:.2f}",
                    "source_url": r.get("source_url", ""),
                }
            )
        else:
            unn = [a for a in areas if best and a["area_id"] == best[0]["area_id"]]
            unmatched.append(
                (
                    cname,
                    aname,
                    f"库内无对应（最接近 {best[0]['name'] if best else '-'} {best[2]:.2f})" if best else "库内该县无片区",
                )
            )

    print(f"== 匹配上 {len(results)} 条 ==")
    for x in results:
        print(
            f"  {x['match_tier']:8s} {x['county_code']} 名单「{x['roster_area_name']}」"
            f" -> {x['matched_area_id']} 库内「{x['area_name']}」[{x['area_status']}] {x['score']}"
        )
    print(f"\n== 未匹配 {len(unmatched)} 条 ==")
    for c, a, why in unmatched:
        print(f"  {c} 「{a}」 — {why}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "roster_county", "county_code", "roster_area_name", "roster_key_village",
                    "matched_area_id", "area_name", "area_status", "match_tier", "score", "source_url",
                ],
            )
            w.writeheader()
            w.writerows(results)
        print(f"\n已写 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
