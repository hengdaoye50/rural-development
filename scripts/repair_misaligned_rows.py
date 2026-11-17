"""修复字段错位与 summary 被日期覆盖两类缺陷。

## 缺陷一：`repair-2026-09` 批次的字段错位（50 行）

该批次把原本带逗号的 `tags` 值写成带引号的单元格，却把紧随其后的
`town_codes` / `cover_desc` / `scale_villages` / `issuer` / `summary`
一并写进了**同一个引号区域**，于是这些值整体落进 `tags` 列，
而 header 对应列位被 `repair-2026-09` 字面量和 `2024-01-01` 占位日期填满。

两类表现：
- **A 型**（41 行）：`town_codes`/`cover_desc`/`scale_villages` 里是批次名或日期
- **B 型**（9 行，浙江）：结构化字段本身是空的，坏在那个「吞掉」的 `tags` 上，
  表现为 `tags` 里混进了镇名和覆盖范围描述

还原规则（实测 A 型 39/40 行的 parts 顺序稳定）：

    [tags...] [town_codes] [cover_desc] [scale_villages] [issuer] [summary] [批次尾标]

`tags` 可能占多段，故先消费「不含镇/乡/街道」的前导段作为 tags，
第一个像镇名的段落作 `town_codes`，其后第一个较长的中文描述作 `cover_desc`，
剩余段中第一个纯数字作 `scale_villages`，最长的一段作 `summary`。

`scale_towns` 与 `issuer` 空槽数量各行不同、无法稳定定位，**一律置空，不猜**。

## 缺陷二：`summary` 被写成日期（78 行）

早期多个批次（JS-batch01 30 行、SH-batch01 16 行、AH-batch01 13 行、
LN-batch01 8 行等）把 `founded_ymd` 的值漏进了 `summary`。
日期不是摘要，一律清空。原始值记入审计 CSV。

## 约束

`cover_desc` 与 `founded_precision` 是 NOT NULL：
`cover_desc` 取不到就保留原值；`founded_precision` 在日期被清空时填 `unknown`
（项目既有约定，见 A650001–A650005 的重建结果）。

用法：
    python scripts/repair_misaligned_rows.py --dry-run
    python scripts/repair_misaligned_rows.py
"""
from __future__ import annotations

import csv
import io
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"
OUT_CSV = ROOT / "reports" / "qa" / "misaligned-rows.csv"
BATCH = "repair-2026-09"
PLACEHOLDER_DATE = "2024-01-01"
UNKNOWN_PRECISION = "unknown"

DATEISH = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:+\-]+)?$")
NUM = re.compile(r"^\d+(\.\d+)?$")
BATCHY = re.compile(r"(repair-\d{4}-\d{2}|batch\d|^[A-Z]{2}-batch|^[A-Z]{2}-(gap|scfjgd))")
TOWNISH = re.compile(r"(镇|乡|街道|苏木)$")
CJK = re.compile(r"[\u4e00-\u9fa5]")
ORGISH = re.compile(r"(组织|政府|局|委|厅|公司|管委会|办事处|党工委|支部|中心)$")

ALL_ABBR = [
    "BJ", "TJ", "HE", "SX", "NM", "LN", "JL", "HL", "SH", "JS", "ZJ", "AH", "FJ",
    "JX", "SD", "HA", "HB", "HN", "GD", "GX", "HI", "CQ", "SC", "GZ", "YN", "XZ",
    "SN", "GS", "QH", "NX", "XJ",
]
FIELDS = ("tags", "town_codes", "cover_desc", "scale_villages", "scale_towns",
          "founded_ymd", "founded_precision", "summary")


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in header})


def junk(v: str) -> bool:
    v = (v or "").strip()
    return bool(v) and (BATCH in v or BATCHY.search(v) is not None or DATEISH.match(v) is not None)


def like_tag(p: str) -> bool:
    """镇名判据必须看**结尾**。用「包含」会把「和美乡村」判成镇名
    （里面有个「乡」），导致 tags 被清空、内容整体错位一格。"""
    p = p.strip()
    return bool(p) and len(p) <= 12 and "，" not in p and "。" not in p and not TOWNISH.search(p)


def misaligned(r: dict[str, str]) -> bool:
    """判据不能只看 tags 里有没有本批次名：各行合并串的尾标不同
    （江苏 `JS-batch02-repair`、青海/宁夏 `Northwest-batch01`、浙江 `ZJ-gap-jh-tz`），
    只查批次名会漏掉一半。硬信号是结构化字段被批次名/日期占位（A 型），
    或 `tags` 被塞进了多段内容（B 型）。"""
    if r.get("created_by") != BATCH:
        return False
    if any(junk(r.get(c, "")) for c in
           ("town_codes", "cover_desc", "scale_villages", "scale_towns", "summary")):
        return True
    return len((r.get("tags") or "").split(",")) >= 3


def repair(r: dict[str, str]) -> None:
    parts = [p.strip() for p in (r.get("tags") or "").split(",")]

    i = 0
    tags: list[str] = []
    while i < len(parts) and like_tag(parts[i]):
        tags.append(parts[i])
        i += 1
    rest = [p for p in parts[i:] if p]
    r["tags"] = ",".join(tags)

    town = ""
    if rest and TOWNISH.search(rest[0]) and len(rest[0]) <= 24:
        town = rest[0]
        rest = rest[1:]
    if junk(r.get("town_codes", "")) or not (r.get("town_codes") or "").strip():
        r["town_codes"] = town if town and not junk(town) else ""

    cover = ""
    if rest and len(rest[0]) >= 6 and CJK.search(rest[0]) and not NUM.match(rest[0]) and not junk(rest[0]):
        cover = rest[0]
        rest = rest[1:]
    # cover_desc 是 NOT NULL：取不到就保留原值，绝不置空
    if (junk(r.get("cover_desc", "")) or NUM.match((r.get("cover_desc") or "").strip())
            or len((r.get("cover_desc") or "").strip()) < 2):
        if cover:
            r["cover_desc"] = cover

    nums = [p for p in rest if NUM.match(p)]
    if junk(r.get("scale_villages", "")) or not (r.get("scale_villages") or "").strip():
        r["scale_villages"] = nums[0] if nums else ""
    if junk(r.get("scale_towns", "")):
        r["scale_towns"] = ""

    if (r.get("founded_ymd") or "").strip() == PLACEHOLDER_DATE:
        r["founded_ymd"] = ""
        r["founded_precision"] = UNKNOWN_PRECISION

    if junk(r.get("summary", "")) or not (r.get("summary") or "").strip():
        # 摘要候选要求够长且不像机构名：短串多是重复的片区名或镇名，
        # 机构名是 issuer 而不是 summary，放错比留空更糟。
        cand = [p for p in rest
                if len(p) >= 12 and p != cover and not NUM.match(p)
                and not junk(p) and not ORGISH.search(p)]
        r["summary"] = max(cand, key=len) if cand else ""


def main() -> int:
    dry = "--dry-run" in sys.argv
    sys.stdout.reconfigure(encoding="utf-8")
    today = date.today().isoformat()
    audit: list[dict[str, str]] = []
    n_fix = n_date = 0

    for abbr in ALL_ABBR:
        f = BY_PROV / f"{abbr}-area.csv"
        if not f.exists():
            continue
        header, rows = read(f)
        hit = 0
        for r in rows:
            before = {c: r.get(c, "") for c in FIELDS}
            kind = ""
            if misaligned(r):
                repair(r)
                kind = "字段错位"
            # 缺陷二对所有行生效：日期不是摘要
            if DATEISH.match((r.get("summary") or "").strip()):
                r["summary"] = ""
                kind = kind or "summary为日期"
            if not kind:
                continue
            if before["summary"] == r.get("summary", "") and kind == "summary为日期":
                continue
            if kind == "summary为日期":
                n_date += 1
            else:
                n_fix += 1
            r["updated_at"] = today
            hit += 1
            rec = {"area_id": r["area_id"], "province_code": r.get("province_code", ""),
                   "name": r["name"], "kind": kind}
            for c in FIELDS:
                rec[f"{c}_before"] = before[c]
                rec[f"{c}_after"] = r.get(c, "")
            audit.append(rec)
        if hit:
            print(f"{abbr}: {hit} 行")
        if not dry and hit:
            write(f, header, rows)

    print(f"\n字段错位 {n_fix} 行；summary 为日期 {n_date} 行；合计 {len(audit)} 行")
    empty_cover = [a for a in audit if not a["cover_desc_after"].strip()]
    if empty_cover:
        print(f"!! cover_desc 仍为空 {len(empty_cover)} 行（会让 build_db 失败）：")
        for a in empty_cover[:10]:
            print(f"   {a['area_id']} {a['name'][:24]}")

    if audit:
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with io.open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(audit[0].keys()))
            w.writeheader()
            w.writerows(audit)
        print(f"审计明细已写 {OUT_CSV}")
    print("\ndry-run，未写盘" if dry else "接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
