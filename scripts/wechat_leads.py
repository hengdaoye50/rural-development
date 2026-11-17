"""用搜狗微信公共搜索抓公众号推文线索（只读、匿名、限速）。

背景：`yichen-unified-search` 的 wechat 路线走 OpenCLI Browser Bridge（需要 daemon +
浏览器扩展），本机没装，路线不可用。本脚本用 HTTP 直读 weixin.sogou.com 达到同一目的，
遵守该 Skill 的边界：只读、匿名、不登录、不碰微信客户端、结果只当线索不当证据。

输出 reports/gaps/wechat-leads-{date}.csv：
  query, title, account, published, snippet, sogou_link

**这些是线索，不是证据**：公众号不是 .gov.cn，按 docs/07 不得进 policy 层；
进 area 前必须找到对应的 .gov.cn 官方文本。

    python scripts/wechat_leads.py "潍坊 乡村振兴 片区" "昌邑 乡村振兴 片区"
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "gaps"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://weixin.sogou.com/weixin?type=2&query="


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://weixin.sogou.com/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse(html: str) -> list[dict[str, str]]:
    rows = []
    # 每条结果：<div class="txt-box"> ... <h3><a ...>标题</a></h3> ... <p class="txt-info">摘要</p>
    #           账号在 <a class="account"> 或 data-share 属性附近；日期在 <span class="s2"> 的 timeConvert
    for block in re.split(r'<li id="sogou_vr_11002601_box_', html)[1:]:
        m_title = re.search(r'<h3>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        m_info = re.search(r'<p class="txt-info"[^>]*>(.*?)</p>', block, re.S)
        m_acct = re.search(r'<a[^>]*class="account"[^>]*>(.*?)</a>', block, re.S)
        if not m_acct:   # 版式变动兜底：账号名常在 s-p 区块的 a 标签里
            m_acct = re.search(r'<div class="s-p"[^>]*>.*?<a[^>]*>(.*?)</a>', block, re.S)
        m_time = re.search(r"timeConvert\('(\d+)'\)", block)
        if not m_title:
            continue
        link = m_title.group(1)
        if link.startswith("/link"):
            link = "https://weixin.sogou.com" + link
        pub = ""
        if m_time:
            pub = time.strftime("%Y-%m-%d", time.localtime(int(m_time.group(1))))
        rows.append({
            "title": strip_tags(m_title.group(2)),
            "account": strip_tags(m_acct.group(1)) if m_acct else "",
            "published": pub,
            "snippet": strip_tags(m_info.group(1)) if m_info else "",
            "sogou_link": link,
        })
    return rows


def main(argv: list[str]) -> int:
    queries = argv or ["潍坊 乡村振兴 片区"]
    all_rows = []
    for i, qq in enumerate(queries):
        try:
            html = fetch(BASE + urllib.parse.quote(qq))
        except Exception as e:
            print(f"  !! {qq}: 抓取失败 {e}")
            continue
        rows = parse(html)
        if not rows:
            print(f"  !! {qq}: 解析到 0 条（可能被反爬）")
        for r in rows:
            r["query"] = qq
        all_rows.extend(rows)
        print(f"  {qq}: {len(rows)} 条")
        if i < len(queries) - 1:
            time.sleep(3)          # 限速，避免触发风控

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"wechat-leads-{date.today().isoformat()}.csv"
    if all_rows:
        merged: dict[tuple[str, str], dict[str, str]] = {}
        if out.exists():                       # 当日多次运行按标题+链接去重合并，不覆盖
            with out.open("r", encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    if r.get("title"):
                        merged[(r["title"], r.get("sogou_link", ""))] = r
        for r in all_rows:
            merged[(r["title"], r["sogou_link"])] = r
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["query", "title", "account", "published",
                                              "snippet", "sogou_link"])
            w.writeheader()
            w.writerows(merged.values())
        print(f"\n本次 {len(all_rows)} 条，累计 {len(merged)} 条 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
