# -*- coding: utf-8 -*-
"""公众号批量采集：按检索式列表跑「搜狗线索 -> 浏览器桥抓正文 -> 落 md/清单」。

用法：
  python scripts/wechat_batch_collect.py --queries "山东 第五批 省级乡村振兴片区" "青海 片区 名单" --top 2
  python scripts/wechat_batch_collect.py --preset thin   # 预置：薄省 + 重点省第五批

产出：
  data/stage/candidates/wechat-md/*.md           每篇正文
  data/stage/candidates/wechat-batch-{date}.csv  批次清单（query/title/url/status/chars/file）
  reports/gaps/wechat-leads-{date}.csv           搜狗线索（由 wechat_leads.py 追加）

限速：搜狗约 50–60 次请求会触发反爬；单次运行建议 ≤10 条检索式。
"""
from __future__ import annotations

import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
CAND = ROOT / "data" / "stage" / "candidates"

PRESETS = {
    "thin": [
        "青海 乡村振兴片区 名单", "宁夏 乡村振兴片区 名单", "新疆 乡村振兴片区 名单",
        "山西 乡村振兴片区 名单", "甘肃 乡村振兴片区 名单", "内蒙古 乡村振兴片区 名单",
    ],
    "sd5": [
        "山东 第五批 省级乡村振兴片区", "山东 乡村振兴片区 公布 2026",
        "济宁 乡村振兴片区 名单", "临沂 乡村振兴片区 名单", "潍坊 乡村振兴片区 名单",
    ],
    "gd": ["广东 镇村片区组团 名单", "广东 第二批 镇村片区组团"],
}


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return f"FAIL rc={r.returncode} {(r.stdout or '')[-200:]}"
    return (r.stdout or "").strip()


def main() -> int:
    args = sys.argv[1:]
    queries: list[str] = []
    if "--preset" in args:
        queries = PRESETS.get(args[args.index("--preset") + 1], [])
    if "--queries" in args:
        i = args.index("--queries")
        for a in args[i + 1:]:
            if a.startswith("--"):
                break
            queries.append(a)
    top = 2
    if "--top" in args:
        top = int(args[args.index("--top") + 1])
    if not queries:
        print("没有检索式。用 --queries 或 --preset thin|sd5|gd")
        return 1

    out = CAND / f"wechat-batch-{date.today().isoformat()}.csv"
    rows: list[dict] = []
    for q in queries:
        print(f"[leads] {q}")
        print("  ", run([PY, str(ROOT / "scripts" / "wechat_leads.py"), q]).splitlines()[-1:] or "")
        print(f"[fetch] {q} top={top}")
        r = run([PY, str(ROOT / "scripts" / "wechat_fetch.py"), "--query", q, "--top", str(top)])
        print("  ", r.splitlines()[-2:] if r else "")

    # 汇总本批 md（按修改时间取今天生成/更新的）
    md_dir = CAND / "wechat-md"
    files = sorted(md_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:top * len(queries)]
    for f in reversed(files):
        t = f.read_text(encoding="utf-8", errors="ignore")
        head = t.splitlines()[0].lstrip("# ").strip() if t else ""
        url = ""
        for line in t.splitlines()[:6]:
            if "http" in line:
                url = line.split("http", 1)[1].strip()
                url = "http" + url
                break
        rows.append({"query": "", "title": head, "url": url, "chars": len(t),
                     "file": str(f.relative_to(ROOT)).replace("\\", "/")})
    with out.open("w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=["query", "title", "url", "chars", "file"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    print(f"OK -> {out.relative_to(ROOT)}（{len(rows)} 篇）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
