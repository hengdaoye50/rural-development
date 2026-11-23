# -*- coding: utf-8 -*-
"""辽宁 docx：抽出超链接（HYPERLINK 域）→ 抓取 → 抽片区候选。"""
from __future__ import annotations

import csv
import re
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(".")
DOCX = Path(r"D:\HuaweiMoveData\Users\zjh22\Desktop\辽宁“片区”链接.docx")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
GEN = ("片区组团", "片区化", "片区发展", "片区建设", "片区治理", "片区党建", "片区项目", "片区名单",
       "片区资源", "片区运营", "片区协作", "片区联动", "片区共建", "片区共富", "片区示范", "片区创建",
       "片区推进", "片区工作", "片区模式", "片区经验", "片区规划", "片区产业", "片区振兴")
LOC = re.compile(r"(镇|村|街道|乡)")
OK = re.compile(r"^[\u4e00-\u9fa5]{2,24}片区$")


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+", "", s)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    z = zipfile.ZipFile(DOCX)
    xml = z.read("word/document.xml").decode("utf-8")
    items = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        urls = re.findall(r'HYPERLINK\s+&quot;([^&]+)&quot;', para)
        text = re.sub(r"<[^>]+>", "", "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S))).strip()
        if urls:
            items.append((text or "(无标题)", urls[0]))
    print(f"超链接 {len(items)} 条")

    region: dict[str, set[str]] = {}
    for line in (ROOT / "data/clean/region.csv").read_text(encoding="utf-8-sig").splitlines()[1:]:
        p = line.split(",")
        if len(p) >= 4 and p[3] == "county":
            region.setdefault(p[1], set()).add(p[0])

    rows, report = [], []
    for i, (title, url) in enumerate(items, 1):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            r.encoding = r.apparent_encoding or "utf-8"
            html = r.text
        except Exception as e:  # noqa: BLE001
            report.append((i, title, url, "抓取失败", str(e)[:40]))
            continue
        body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
        body = re.sub(r"<[^>]+>", "\n", body)
        body = re.sub(r"[ \t\u3000]+", " ", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        d = ROOT / "data" / "raw" / "LN" / f"2026-ln-{i:02d}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "原文.md").write_text(body, encoding="utf-8")
        found = []
        for m in re.finditer(r"([\u4e00-\u9fa5]{2,24}?片区)", body):
            name = m.group(1)
            if any(name == g or name.endswith(g) for g in GEN) or len(name) < 4:
                continue
            if not LOC.search(name):
                continue
            if not OK.match(name):
                continue
            found.append(name)
        uniq = list(dict.fromkeys(found))
        report.append((i, title, url, f"{len(body)} 字", f"片区候选 {len(uniq)}: {', '.join(uniq[:6])}"))
        for name in uniq:
            code, county = "", ""
            for nm, codes in region.items():
                if nm in name and len(nm) >= 2 and len(codes) == 1:
                    code, county = next(iter(codes)), nm
                    break
            rows.append({"idx": i, "title": title, "url": url, "name": name,
                         "county": county, "code": code,
                         "local_path": str(d.relative_to(ROOT)) + "/原文.md"})
        print(f"{i:02d} {len(body):5d}字 {len(uniq):2d}候选 | {title[:40]}")

    out = ROOT / "data/stage/candidates/ln-links-extract.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["idx", "title", "url", "name", "county", "code", "local_path"],
                           lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    fmt = ROOT / "reports/qa/辽宁链接核查.md"
    with fmt.open("w", encoding="utf-8") as f:
        f.write("# 辽宁「片区」链接核查\n\n")
        f.write(f"共 {len(items)} 条链接，抓取成功 {sum(1 for r in report if '字' in r[3])} 条。\n\n")
        f.write("| # | 标题 | 状态 | 说明 |\n|---|---|---|---|\n")
        for i, title, url, st, note in report:
            f.write(f"| {i} | [{title[:38]}]({url}) | {st} | {note[:80]} |\n")
    print(f"\n候选 {len(rows)} 行 -> {out.relative_to(ROOT)}｜报告 {fmt.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
