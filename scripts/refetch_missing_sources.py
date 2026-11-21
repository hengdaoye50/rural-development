# -*- coding: utf-8 -*-
"""补采无快照来源：对 excerpt_status='missing' 的 source，抓 URL 正文存 raw 并回填 local_path/hash。

复用 `fetch_gov_doc.py` 的抓取与正文提取（非 .gov.cn 也允许，因为这是 `source` 层，
不违反政策层白名单；媒体稿只能进 source）。

用法：python scripts/refetch_missing_sources.py [--limit 20] [--dry-run]
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "data" / "clean" / "by_province"
RAW = ROOT / "data" / "raw"


def load_fetch():
    spec = importlib.util.spec_from_file_location("fgd", ROOT / "scripts" / "fetch_gov_doc.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["fgd"] = m
    spec.loader.exec_module(m)  # type: ignore[union-attr]
    return m


def read(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p, hdr, rows):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    os.replace(tmp, p)


def slug(s: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", s or "").strip("-")
    return (s or "src")[:40]


def main() -> int:
    dry = "--dry-run" in sys.argv
    limit = 20
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    fgd = load_fetch()
    todo = []
    for sp in sorted(BP.glob("*-source.csv")):
        hdr, rows = read(sp)
        for s in rows:
            if (s.get("excerpt_status") or "") == "missing" and (s.get("url") or "").startswith("http"):
                todo.append((sp, s))
    print(f"待补采 {len(todo)} 条，本轮处理 {min(limit, len(todo))} 条")
    ok = fail = 0
    for sp, s in todo[:limit]:
        url = s["url"]
        try:
            try:
                html = fgd.fetch(url)
            except ValueError as ve:
                if "非 .gov.cn" not in str(ve):
                    raise
                # source 层允许媒体：绕开政策层白名单，直接用 UA 抓 HTML
                import urllib.request
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
                with urllib.request.urlopen(req, timeout=25) as resp:
                    html = resp.read().decode("utf-8", "ignore")
            body = fgd.body_of(html, s.get("title") or "")
            if fgd.cn_chars(body) < 150:
                raise ValueError(f"正文过短 {fgd.cn_chars(body)} 汉字")
        except Exception as e:  # noqa: BLE001
            print("  ✗", s["source_id"], type(e).__name__, str(e)[:60])
            fail += 1
            continue
        abbr = sp.name.split("-")[0]
        d = RAW / abbr / f"{date.today():%Y%m%d}-{slug(s.get('title') or s['source_id'])}"
        d.mkdir(parents=True, exist_ok=True)
        f = d / "原文.md"
        if dry:
            print("  ~", s["source_id"], "->", d.relative_to(ROOT))
            ok += 1
            continue
        # newline="\n" 防止 Windows 文本模式把 LF 写坏，哈希才与文件一致
        with f.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        hdr, rows = read(sp)
        for r in rows:
            if r.get("source_id") == s["source_id"]:
                r["local_path"] = str(f.relative_to(ROOT)).replace("\\", "/")
                r["hash_sha256"] = digest
                r["fetched_at"] = date.today().isoformat()
                r["excerpt_status"] = "verbatim" if (r.get("excerpt") or "").strip() and \
                    (r["excerpt"].strip() in body or re.sub(r"\s", "", r["excerpt"]) in re.sub(r"\s", "", body)) else "digest"
        write(sp, hdr, rows)
        ok += 1
        print("  ✓", s["source_id"], "->", f.relative_to(ROOT))
    print(f"成功 {ok} / 失败 {fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
