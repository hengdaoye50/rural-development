"""用民政部《县以上行政区划代码》补 `data/clean/region.csv` 的占位行。

占位行指 `name == region_code` 的行（采集时以 `aliases=auto` 自动插入、无真实名称）。
只补 `name`/`short_name`；`region_code`/`parent_code`/`level` 一律原样保留；
已有真实名称（`name != region_code`）的行不覆盖。

权威源：民政部 mca.gov.cn 逐年《中华人民共和国县以上行政区划代码》公告页，
即 GB/T 2260 代码表。抓不到源则直接非零退出，不使用记忆中的区划表填充。

用法：
    python scripts/fetch_region_codes.py            # 补占位行并写回 region.csv
    python scripts/fetch_region_codes.py --dry-run  # 只打印结果，不写文件
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html as htmllib
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION = ROOT / "data" / "clean" / "region.csv"
AREA = ROOT / "data" / "clean" / "area.csv"
QA_DIR = ROOT / "reports" / "qa"

FIELDS = ["region_code", "name", "short_name", "level", "parent_code", "aliases"]

# 新→旧排序：先取到新年份的码，旧年份只兜底
SOURCES = [
    ("2023", "https://www.mca.gov.cn/mzsj/xzqh/2023/202301xzqh.html"),
    ("2022", "https://www.mca.gov.cn/mzsj/xzqh/2022/202201xzqh.html"),
    ("2021", "https://www.mca.gov.cn/mzsj/xzqh/2021/202101xzqh.html"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "close",
}

CODE_RE = re.compile(r"^\d{6}$")


def fetch(url: str, attempts: int = 3, timeout: int = 60) -> str:
    last = ""
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            for enc in ("utf-8", "gb18030"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - 网络错误一律重试后上报
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"抓取失败 {url} :: {last}")


def parse_pairs(page: str) -> dict[str, str]:
    """把公告页解析成 {六位码: 名称}。

    页面结构是一张 Excel 风格的平表，去标签后得到交替出现的
    `代码, 名称` 文本片段，按相邻关系配对。
    """
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", page)
    text = re.sub(r"(?s)<[^>]+>", "\n", text)
    text = htmllib.unescape(text).replace("\xa0", " ")
    parts = [p.strip() for p in text.split("\n")]
    parts = [p for p in parts if p]

    out: dict[str, str] = {}
    i = 0
    while i < len(parts) - 1:
        code, name = parts[i], parts[i + 1]
        if CODE_RE.match(code) and not CODE_RE.match(name) and not re.search(r"\d", name):
            # 民政部用「*」标注省直辖县级行政区，星号是排版标记，不入名称
            out[code] = name.rstrip("*").strip()
            i += 2
        else:
            i += 1
    return out


def load_sources() -> tuple[dict[str, str], dict[str, str], list[str]]:
    """返回 ({code: name}, {code: 来源年份}, 抓取记录)。新年份优先。"""
    names: dict[str, str] = {}
    origin: dict[str, str] = {}
    log: list[str] = []
    for year, url in SOURCES:
        try:
            page = fetch(url)
        except RuntimeError as exc:
            log.append(f"- {year} `{url}` 抓取失败：{exc}")
            continue
        pairs = parse_pairs(page)
        log.append(f"- {year} `{url}` 解析出 {len(pairs)} 条")
        if len(pairs) < 2000:
            log.append(f"  - 条数异常偏少（<2000），本年份不作为主源")
            continue
        for code, name in pairs.items():
            if code not in names:
                names[code] = name
                origin[code] = year
    return names, origin, log


def read_region() -> list[dict[str, str]]:
    with REGION.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def province_names(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        r["region_code"][:2]: r["name"]
        for r in rows
        if r.get("level") == "province" and r.get("name") and r["name"] != r["region_code"]
    }


def placeholder_usage(codes: set[str]) -> dict[str, int]:
    """统计 area 表里仍在引用这些占位码的记录数（按 code）。"""
    if not AREA.exists():
        return {}
    used: dict[str, int] = {}
    with AREA.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            for field in ("city_code", "county_code"):
                code = row.get(field) or ""
                if code in codes:
                    used[code] = used.get(code, 0) + 1
    return used


def area_region_refs() -> set[str]:
    """area 表引用到的全部市/县级码（去重）。"""
    if not AREA.exists():
        return set()
    refs: set[str] = set()
    with AREA.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            for field in ("city_code", "county_code"):
                code = (row.get(field) or "").strip()
                if CODE_RE.match(code):
                    refs.add(code)
    return refs


def infer_hierarchy(code: str) -> tuple[str, str] | None:
    """按 GB/T 2260 编码规则推断 (level, parent_code)。"""
    if code.endswith("0000"):
        return None  # 省级，不在此处新增
    if code[2:4] == "00":
        return "city", code[:2] + "0000"
    if code[4:] == "00":
        return "county", code[:2] + "0000"  # 省直辖县级（469000 一类）
    return "county", code[:4] + "00"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写 region.csv")
    args = ap.parse_args()

    rows = read_region()
    authoritative, origin, log = load_sources()
    if not authoritative:
        print("未取到任何权威源，放弃（不使用记忆区划表填充）", file=sys.stderr)
        for line in log:
            print(line, file=sys.stderr)
        return 2
    print(f"权威源合计 {len(authoritative)} 个码")

    prov = province_names(rows)
    filled: list[tuple[str, str, str]] = []
    stale_src: list[tuple[str, str, str]] = []
    missing: list[str] = []

    for row in rows:
        code = row["region_code"]
        if row.get("name") != code:
            continue  # 已有真实名称，绝不覆盖
        name = authoritative.get(code)
        if not name:
            missing.append(code)
            continue
        row["name"] = name
        record = (code, name, origin.get(code, "?"))
        filled.append(record)
        if origin.get(code) != SOURCES[0][0]:
            stale_src.append(record)

    by_prov: dict[str, int] = {}
    for code in missing:
        label = prov.get(code[:2], code[:2])
        by_prov[label] = by_prov.get(label, 0) + 1

    # region 缺行、但 area 已在引用的码：按权威源补行，否则外键悬空
    existing = {r["region_code"] for r in rows}
    added: list[tuple[str, str, str]] = []
    unresolved: list[str] = []
    for code in sorted(area_region_refs() - existing):
        name = authoritative.get(code)
        hier = infer_hierarchy(code)
        if not name or not hier:
            unresolved.append(code)
            continue
        level, parent = hier
        rows.append(
            {
                "region_code": code,
                "name": name,
                "short_name": "",
                "level": level,
                "parent_code": parent,
                "aliases": "auto",
            }
        )
        added.append((code, name, level))

    if not args.dry_run:
        with REGION.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k, "") for k in FIELDS})

    today = dt.date.today().isoformat()
    lines = [
        f"# region 名称补全 · {today}",
        "",
        f"- 源：民政部《中华人民共和国县以上行政区划代码》公告页（GB/T 2260）",
        f"- region.csv 总行 {len(rows)}；本次补名 {len(filled)} 行；新增 {len(added)} 行；仍为占位 {len(missing)} 行",
        f"- 已写入：{'否（--dry-run）' if args.dry_run else str(REGION.relative_to(ROOT))}",
        "",
        "## 抓取记录",
        "",
        *log,
        "",
        "## 仍为占位的代码（权威源无此码：已撤销/开发区码/自造码，未编造名称）",
        "",
    ]
    if missing:
        lines.append("按省计数：")
        lines.append("")
        for label, cnt in sorted(by_prov.items(), key=lambda kv: -kv[1]):
            lines.append(f"- {label}：{cnt}")
        lines.append("")
        lines.append("清单：")
        lines.append("")
        lines.append("、".join(f"`{c}`{prov.get(c[:2], '')}" for c in missing))
        used = placeholder_usage(set(missing))
        if used:
            lines.append("")
            lines.append("其中仍被 `area` 引用的码（本次按约束未改 area）：")
            lines.append("")
            for code, cnt in sorted(used.items(), key=lambda kv: -kv[1]):
                lines.append(f"- `{code}`（{prov.get(code[:2], '')}）：{cnt} 条 area")
    else:
        lines.append("无")

    lines += ["", "## 按 area 引用补建的行（region 原缺此码）", ""]
    if added:
        for code, name, level in added:
            lines.append(f"- `{code}` {name}（{level}）")
    else:
        lines.append("无")
    if unresolved:
        lines += ["", "以下码被 `area` 引用、`region` 缺行，且权威源无此码，未补建（外键会悬空，需人工裁定）：", ""]
        lines.append("、".join(f"`{c}`" for c in unresolved))

    lines += ["", "## 仅旧年份源命中（新年份源已无此码，可能已撤销/改码）", ""]
    if stale_src:
        for code, name, year in stale_src:
            lines.append(f"- `{code}` {name}（{year} 年源）")
    else:
        lines.append("无")

    lines += ["", "## 说明", "", "- `short_name` 未动：苏浙鲁沪皖闽赣的真实名称行亦为空，保持文件同构；需要简称时走 `data/stage/region-patch.csv`。"]
    lines.append("- `region_code`/`parent_code`/`level` 未改动；`area` 表未触碰。")

    QA_DIR.mkdir(parents=True, exist_ok=True)
    report = QA_DIR / f"region-fetch-{today.replace('-', '')}.md"
    if not args.dry_run:
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"补名 {len(filled)} 行，新增 {len(added)} 行，仍占位 {len(missing)} 行")
    for code, name, level in added:
        print(f"  新增 {code} {name} ({level})")
    if unresolved:
        print(f"  待裁定（area 引用但 region 缺行且无权威名称）: {unresolved}")
    for label, cnt in sorted(by_prov.items(), key=lambda kv: -kv[1]):
        print(f"  仍占位 {label}: {cnt}")
    if stale_src:
        print(f"  旧年源命中 {len(stale_src)} 行")
    print("报告", report.relative_to(ROOT) if not args.dry_run else "(dry-run 未写)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
