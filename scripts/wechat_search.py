# -*- coding: utf-8 -*-
"""公众号检索（搜狗微信，走 OpenCLI 浏览器桥）→ 结果列表 / 打开正文存档。

为什么不用 requests：搜狗微信对直连 IP 反爬（返回 0 条）；浏览器桥带真实会话，能直出结果。
为什么走浏览器：/link?url=… 是搜狗跳转链，只有在浏览器里打开才会落到 mp.weixin 正文。

用法：
  # 只列结果（标题/日期/摘要/链接）
  python scripts/wechat_search.py "第五批省级乡村振兴片区 名单"
  python scripts/wechat_search.py "鲁农组办发 2026 14号" --pages 2

  # 打开第 N 条结果并落盘原文（缺省 data/raw/WX/{date}-{slug}/原文.md）
  python scripts/wechat_search.py "第五批省级乡村振兴片区 名单" --open 3 --abbr SD

  # 打开前 N 条（按顺序）
  python scripts/wechat_search.py "…" --open 1,2,4 --abbr SD

产出：data/raw/{ABBR}/{date}-{slug}/原文.md + meta.json；
      data/stage/candidates/wechat-search-{date}.csv（query/title/date/url/file）
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
import urllib.parse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data" / "stage" / "candidates"
NODE = "node"
MAIN_JS = str(Path(os.path.expandvars(r"%USERPROFILE%")) /
              r"scoop\apps\nodejs-lts\current\bin\node_modules\@jackwener\opencli\dist\src\main.js")

RESULT_JS = (
    "JSON.stringify(Array.from(document.querySelectorAll('li'))"
    ".filter(function(li){return li.querySelector('h3 a');})"
    ".map(function(li){var a=li.querySelector('h3 a');"
    "var p=li.querySelector('p.txt-info');var s=li.querySelector('span.s2');"
    "var sp=li.querySelector('.s-p')||li.querySelector('.txt-box');"
    "return [a.textContent.trim(), a.href, s?s.innerHTML:'',"
    "p?p.textContent.trim().replace(/\\s+/g,' ').slice(0,90):'',"
    "sp?sp.innerText.replace(/\\s+/g,' ').trim():''];}))"
)

# 政府号 / 媒体号 / 自媒体 三档（入 policy 只认政府号，见 docs/07 §3）
GOV_HINTS = ("农业农村", "人民政府", "乡村振兴局", "农办", "政务", "党建", "发展改革",
             "财政", "水利", "发布", "政府", "三农")
MEDIA_HINTS = ("日报", "晚报", "党报", "电视台", "广播", "融媒", "新闻网", "报业",
               "通讯社", "新华", "人民网", "大众", "齐鲁", "新媒体", "网信")
SELF_MEDIA_HINTS = ("农畔", "团队", "咨询", "服务商", "小编", "阿农", "乡村运营",
                    "信息科技", "设计集团", "研究所", "智库")


def account_kind(acc: str) -> str:
    a = acc or ""
    if any(h in a for h in SELF_MEDIA_HINTS):
        return "自媒体?"
    if any(h in a for h in MEDIA_HINTS):
        return "媒体号"
    if any(h in a for h in GOV_HINTS):
        return "政府号"
    return "待核"


def cli(*args: str) -> str:
    r = subprocess.run([NODE, MAIN_JS, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return r.stdout or ""


def jload(raw: str, kind: list | dict = list):
    """从 cli 输出里抠出第一段 JSON（opencli 会混入 update 提示）。"""
    i = raw.find("[") if kind is list else raw.find("{")
    if i < 0:
        return kind()
    try:
        return json.loads(raw[i:])
    except json.JSONDecodeError:
        return kind()


def slug(s: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", s or "").strip("-")
    return (s or "wx")[:40]


def epoch_to_date(html: str) -> str:
    m = re.search(r"timeConvert\('(\d+)'\)", html or "")
    return time.strftime("%Y-%m-%d", time.localtime(int(m.group(1)))) if m else ""


def search(query: str, pages: int) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, pages + 1):
        url = ("https://weixin.sogou.com/weixin?type=2&ie=utf8&query="
               + urllib.parse.quote(query) + (f"&page={page}" if page > 1 else ""))
        cli("browser", "main", "open", url)
        time.sleep(6)
        data = jload(cli("browser", "main", "eval", RESULT_JS), list)
        for t, href, d, snip, sp in data:
            # .s-p 文本形如「农畔 2026-3-14」；拆出账号与日期
            m = re.search(r"^(.*?)\s*(\d{4}-\d{1,2}-\d{1,2})\s*$", sp or "")
            acc = (m.group(1) if m else (sp or "")).strip()
            rows.append({"title": t, "href": href, "date": epoch_to_date(d),
                         "snippet": snip, "account": acc, "kind": account_kind(acc), "page": page})
        print(f"  第 {page} 页：{len(data)} 条")
    return rows


def open_article(href: str, abbr: str) -> dict | None:
    """打开搜狗跳转链 → 落到 mp.weixin 正文 → 抽取并落盘。"""
    cli("browser", "main", "open", href)
    time.sleep(8)
    state = jload(cli("browser", "main", "extract"), dict)
    title = state.get("title", "") or ""
    text = state.get("content", "") or ""
    if "微信公众平台" in title or len(text) < 200:
        time.sleep(6)
        state = jload(cli("browser", "main", "extract"), dict)
        title = state.get("title", "") or title
        text = state.get("content", "") or text
    if not text or len(text) < 200:
        print(f"  ✗ 正文过短：{title[:30]}")
        return None
    url = state.get("url", "")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    d = ROOT / "data" / "raw" / abbr / f"{date.today():%Y%m%d}-{slug(title)}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "原文.md").write_text(text, encoding="utf-8", newline="\n")
    (d / "meta.json").write_text(json.dumps({
        "url": url, "title": title, "source_kind": "公众号", "abbr": abbr,
        "fetched_at": date.today().isoformat(), "chars": len(text),
        "via": "sogou-wechat-browser",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ✓ {title[:36]} | {len(text)} 字 -> {d.name}")
    return {"title": title, "url": url, "file": str((d / "原文.md").relative_to(ROOT)).replace("\\", "/"),
            "chars": len(text)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--open", default="", help="要打开的序号，逗号分隔，如 1,2,5")
    ap.add_argument("--abbr", default="WX")
    ap.add_argument("--all", action="store_true",
                    help="连自媒体号也打开（默认只打开官方/媒体号；自媒体只列不采）")
    ap.add_argument("--queries-file", default="",
                    help="批量模式：每行一个检索式，自动打开每条的第一个政府号（无则媒体号）")
    args = ap.parse_args()

    saved = []
    if args.queries_file:
        qs = [x.strip() for x in Path(args.queries_file).read_text(encoding="utf-8").splitlines()
              if x.strip() and not x.startswith("#")]
        print(f"批量检索 {len(qs)} 条")
        for q in qs:
            print(f"\n=== {q}")
            rows = search(q, 1)
            for i, r in enumerate(rows, 1):
                print(f"{i:2d}. [{r['kind']}] {r['account'][:12]:12s}｜{r['title'][:40]}")
            pick = next((r for r in rows if r["kind"] == "政府号"), None)
            if not pick:
                pick = next((r for r in rows if r["kind"] == "媒体号"), None)
            if not pick:
                print("  → 无政府号/媒体号结果，跳过")
                continue
            print(f"  → 打开 [{pick['kind']}] {pick['account']}｜{pick['title'][:34]}")
            got = open_article(pick["href"], args.abbr)
            if got:
                saved.append({**got, "query": q, "date": pick["date"], "account": pick["account"]})
            time.sleep(2)
    else:
        print(f"检索：{args.query}")
        rows = search(args.query, args.pages)
        for i, r in enumerate(rows, 1):
            print(f"{i:2d}. [{r['kind']}] {r['account'][:12]:12s}｜{r['title'][:40]}  [{r['date']}]")
        if not rows:
            print("没有结果（可能触发反爬，换时间/换词再试）")
            return 1

        if args.open:
            want = [int(x) for x in re.split(r"[,，\s]+", args.open.strip()) if x.strip().isdigit()]
            for k in want:
                if not (1 <= k <= len(rows)):
                    print(f"  跳过 {k}：超出范围")
                    continue
                r = rows[k - 1]
                if r["kind"] == "自媒体?" and not args.all:
                    print(f"  跳过 #{k}（{r['account']} 属自媒体/服务商，需 --all 才采）")
                    continue
                print(f"打开 #{k} [{r['account']}] {r['title'][:36]}")
                got = open_article(r["href"], args.abbr)
                if got:
                    saved.append({**got, "query": args.query, "date": r["date"],
                                  "account": r["account"]})
                time.sleep(3)

    if saved:
        out = CAND / f"wechat-search-{date.today().isoformat()}.csv"
        new = not out.exists()
        with out.open("a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["query", "account", "title", "date", "url", "file", "chars"],
                               lineterminator="\r\n")
            if new:
                w.writeheader()
            for s in saved:
                w.writerow({k: s.get(k, "") for k in w.fieldnames})
        print(f"已记录 {len(saved)} 条 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
