"""探测失效来源的 URL 是否仍可访问。只读，不写任何文件。

用法：
  python scripts/probe_dead_sources.py                 # 探测全部
  python scripts/probe_dead_sources.py --limit 20      # 先试 20 条
  python scripts/probe_dead_sources.py --csv reports/qa/dead-source-probe.csv
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def probe(url: str, timeout: int = 15) -> tuple[str, str]:
    """返回 (状态, 说明)。状态：alive / http_4xx / http_5xx / error / skip"""
    if not url or not url.startswith("http"):
        return "skip", "非 http URL"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(4096)
            return "alive", f"{r.status} {r.headers.get('Content-Type','')[:40]} {len(data)}B+"
    except urllib.error.HTTPError as e:
        return ("http_4xx" if 400 <= e.code < 500 else "http_5xx"), f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 网络异常种类多，统一归类
        return "error", type(e).__name__


def main() -> int:
    args = sys.argv[1:]
    limit = 0
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    to_csv = ""
    if "--csv" in args:
        to_csv = args[args.index("--csv") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = [
        r for r in conn.execute(
            "select source_id, area_id, url, title, publisher, published_ymd, "
            "credibility, local_path from source"
        )
        if r["local_path"] and not os.path.exists(r["local_path"])
    ]
    if limit:
        rows = rows[:limit]

    print(f"探测 {len(rows)} 条失效来源 ...")
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(probe, r["url"]): r for r in rows}
        for i, fut in enumerate(as_completed(futs), 1):
            r = futs[fut]
            st, note = fut.result()
            results.append({
                "source_id": r["source_id"], "status": st, "note": note,
                "credibility": r["credibility"], "url": r["url"],
                "title": r["title"], "local_path": r["local_path"],
            })
            if i % 20 == 0:
                print(f"  {i}/{len(rows)}")

    from collections import Counter
    stat = Counter(x["status"] for x in results)
    print("\n探测结果：")
    for k, v in stat.most_common():
        print(f"  {k:10s} {v:4d}")

    alive = [x for x in results if x["status"] == "alive"]
    if alive:
        print(f"\n可恢复 {len(alive)} 条，其中 A 级 {sum(1 for x in alive if x['credibility']=='A')} 条")
        for x in alive[:15]:
            print(f"  {x['source_id']:9s} [{x['credibility']}] {x['title'][:40]}")

    if to_csv:
        out = ROOT / to_csv
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["source_id", "status", "note", "credibility",
                                              "url", "title", "local_path"])
            w.writeheader()
            w.writerows(sorted(results, key=lambda x: (x["status"], x["source_id"])))
        print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
