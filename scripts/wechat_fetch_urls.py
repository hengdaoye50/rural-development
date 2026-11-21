# -*- coding: utf-8 -*-
"""按 URL 批量抓公众号正文（OpenCLI Browser Bridge）。

比搜狗查询更准：URL 由搜索引擎/agent 找到，正文由桥抓取，落 raw 归档。

用法：
  python scripts/wechat_fetch_urls.py --urls "https://mp.weixin.qq.com/s?..." "https://..."
  python scripts/wechat_fetch_urls.py --file data/stage/candidates/wechat-urls.txt --abbr SD

产出：
  data/raw/{ABBR}/{date}-{slug}/原文.md + meta.json
  data/stage/candidates/wechat-urls-{date}.csv（url/title/chars/file）
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data" / "stage" / "candidates"


def _ps(cmd: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return r.stdout or ""


def extract(url: str) -> tuple[str, str]:
    """返回 (title, markdown_text)。opencli 在 Windows 是 .ps1 shim，必须经 PowerShell 调。"""
    _ps(f"opencli browser main open '{url}' --window background")
    out = _ps("opencli browser main extract")
    try:
        d = json.loads(out[out.index("{"):]) if "{" in out else {}
    except Exception:  # noqa: BLE001
        d = {}
    return d.get("title", ""), d.get("content", "")


def slug(s: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", s or "").strip("-")
    return (s or "wx")[:40]


def main() -> int:
    args = sys.argv[1:]
    urls: list[str] = []
    abbr = "WX"
    if "--abbr" in args:
        abbr = args[args.index("--abbr") + 1]
    if "--file" in args:
        p = Path(args[args.index("--file") + 1])
        urls += [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip().startswith("http")]
    if "--urls" in args:
        i = args.index("--urls")
        for a in args[i + 1:]:
            if a.startswith("--"):
                break
            if a.startswith("http"):
                urls.append(a)
    if not urls:
        print("没有 URL")
        return 1

    rows = []
    for url in urls:
        title, text = extract(url)
        if not text or len(text) < 200:
            print("  ✗ 抓取失败/过短:", url[:60])
            continue
        text = re.sub(r"!\[图片\]\([^)]*\)", "", text)          # 去图片
        text = re.sub(r"!\[\]\([^)]*\)", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        d = ROOT / "data" / "raw" / abbr / f"{date.today():%Y%m%d}-{slug(title)}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "原文.md").write_text(text, encoding="utf-8", newline="\n")
        (d / "meta.json").write_text(json.dumps({
            "url": url, "title": title, "source_kind": "公众号", "abbr": abbr,
            "fetched_at": date.today().isoformat(), "chars": len(text),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        rows.append({"url": url, "title": title, "chars": len(text),
                     "file": str((d / "原文.md").relative_to(ROOT)).replace("\\", "/")})
        print(f"  ✓ {title[:40]} | {len(text)} 字 -> {d.name}")

    out = CAND / f"wechat-urls-{date.today().isoformat()}.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["url", "title", "chars", "file"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK {len(rows)}/{len(urls)} -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
