# -*- coding: utf-8 -*-
"""批量抓取广东/陕西清单页面，抽取「XX片区」候选 + 县区归属（只读产出，不入库）。

输入：广东 md 链接清单、陕西 docx 链接清单
输出：
  data/raw/GD|SN/<date>-<slug>/原文.md
  data/stage/candidates/gd-sn-extract.csv
  reports/qa/粤陕清单抽取-预览.md
"""
from __future__ import annotations

import csv
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+")

GEN_TAIL = ("片区组团", "片区化", "片区发展", "片区建设", "片区治理", "片区党建", "片区联合",
            "片区项目", "片区名单", "片区资源", "片区运营", "片区协作", "片区联动", "片区共建",
            "片区共富", "片区示范", "片区创建", "片区推进", "片区工作", "片区模式", "片区经验",
            "片区规划", "片区产业", "片区振兴", "片区组团式", "片区内", "片区外")
PAT = re.compile(r"([\u4e00-\u9fa5A-Za-z0-9·]{2,18}?片区)")


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def clean_html(html: str) -> str:
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</p>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"&nbsp;", " ", body)
    body = re.sub(r"&amp;", "&", body)
    body = re.sub(r"[ \t\u3000]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    md = ROOT.parent / ".."  # placeholder
    gd_file = Path(r"D:\HuaweiMoveData\Users\zjh22\Desktop\广东片区链接.md")
    sn_file = Path(r"D:\HuaweiMoveData\Users\zjh22\Desktop\陕西.docx")

    urls: list[tuple[str, str, str]] = []  # (abbr, url, title)
    for line in gd_file.read_text(encoding="utf-8").splitlines():
        u = line.strip().replace("\\_", "_")
        if u.startswith("http"):
            urls.append(("GD", u, ""))
    with zipfile.ZipFile(sn_file) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, re.S)).strip()
        if t.startswith("http"):
            urls.append(("SN", t, ""))
    seen, uniq = set(), []
    for a, u, t in urls:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((a, u, t))
    print(f"URL 共 {len(uniq)} 条（GD {sum(1 for x in uniq if x[0]=='GD')} / SN {sum(1 for x in uniq if x[0]=='SN')}）")

    # 县区名 -> 码（同名取唯一，歧义丢弃）
    names: dict[str, str | None] = {}
    for line in (ROOT / "data/clean/region.csv").read_text(encoding="utf-8-sig").splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 4 or parts[3] != "county":
            continue
        nm = parts[1]
        names[nm] = parts[0] if nm not in names else None

    rows = []
    today = date.today().isoformat()
    for abbr, url, _ in uniq:
        try:
            r = requests.get(url, headers=UA, timeout=30)
            r.encoding = r.apparent_encoding or "utf-8"
            html = r.text
        except Exception as e:  # noqa: BLE001
            print(f"ERR {url} {e}")
            continue
        title_m = re.search(r"<title>(.*?)</title>", html, re.S)
        title = re.sub(r"\s+", "", title_m.group(1)) if title_m else ""
        text = clean_html(html)
        slug = re.sub(r"[^0-9A-Za-z]+", "-", url.rstrip("/").split("/")[-1])[:40] or "page"
        d = ROOT / "data" / "raw" / abbr / f"{today}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "原文.md").write_text(text, encoding="utf-8")
        # 候选
        cands = {}
        for m in PAT.finditer(text):
            t = m.group(1)
            if any(t.endswith(g) or t == g for g in GEN_TAIL):
                continue
            if len(t) < 4:
                continue
            start = max(0, m.start() - 60)
            ctx = text[start:m.end() + 60]
            county, code = "", ""
            for nm, cd in names.items():
                if cd and nm in ctx and len(nm) >= 2:
                    county, code = nm, cd
                    break
            if not county:
                for nm, cd in names.items():
                    if cd and nm in title and len(nm) >= 2:
                        county, code = nm, cd
                        break
            cands.setdefault(t, {"name": t, "county": county, "county_code": code,
                                 "excerpt": re.sub(r"\s+", "", ctx)[:160]})
        for c in cands.values():
            rows.append({"abbr": abbr, "url": url, "title": title, "local_path": str(d.relative_to(ROOT)),
                         **c})
        print(f"{abbr} {len(cands):2d} 候选 | {title[:34]}")

    out = ROOT / "data/stage/candidates/gd-sn-extract.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["abbr", "name", "county", "county_code", "excerpt",
                                          "url", "title", "local_path"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    named = sum(1 for r in rows if r["county_code"])
    print(f"\n候选 {len(rows)} 条，其中县区可判定 {named} 条 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
