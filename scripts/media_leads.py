"""批量采集「县 × 片区」的媒体与融媒线索（只做发现，不做证据）。

为什么需要它：政府站覆盖有限，县级融媒体中心与政务号往往先报道本地片区，
但**它们不是 .gov.cn，按 docs/07 进不了 policy 层**，只能作 source 线索或待核依据。

通道（均为公开只读、匿名、限速）：
- `sogou-wechat`：weixin.sogou.com，公众号文章（有临时跳转链，正文需另取）
- `sogou-web`：www.sogou.com/web，普通网页（含县级融媒站、党报客户端）

输入：缺县清单 CSV（默认 reports/gaps/coverage-gaps.csv），或 --counties 指定县码。
输出：data/stage/candidates/media-leads-{YYYY-MM-DD}.csv，按县码+标题去重合并。

    python scripts/media_leads.py --limit 8
    python scripts/media_leads.py --counties 140521,360203 --channels sogou-wechat
    python scripts/media_leads.py --from-code 200 --limit 100     # 分批续跑
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
GAPS = ROOT / "reports" / "gaps" / "coverage-gaps.csv"
OUT_DIR = ROOT / "data" / "stage" / "candidates"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TERMS = ("片区", "示范带", "示范片", "组团片区", "样板带", "示范区")
# 城市/工业语境不是本研究对象（docs/01 §3 排除项），命中这些词直接丢弃
EXCLUDE = ("成片开发", "土地征收", "征收成片", "控规", "控制性详细规划", "产业园", "工业园区",
           "开发区", "风景名胜区", "棚户区", "老旧小区", "供水", "污水处理")
SLEEP = 6.0            # 实测：3 秒在 50 次请求后触发搜狗反爬，放慢到 6 秒
BLOCK_SLEEP = 90       # 命中反爬后冷却
MAX_CONSECUTIVE_BLOCK = 3


def is_blocked(html: str) -> bool:
    return ("antispider" in html) or ("请输入验证码" in html) or ("您的访问过于频繁" in html)


def fetch(url: str, referer: str = "https://weixin.sogou.com/") -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": referer,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def parse_wechat(html: str) -> list[dict[str, str]]:
    out = []
    for block in re.split(r'<li id="sogou_vr_11002601_box_', html)[1:]:
        m = re.search(r'<h3>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        info = re.search(r'<p class="txt-info"[^>]*>(.*?)</p>', block, re.S)
        acct = re.search(r'<a[^>]*class="account"[^>]*>(.*?)</a>', block, re.S)
        t = re.search(r"timeConvert\('(\d+)'\)", block)
        link = m.group(1)
        if link.startswith("/link"):
            link = "https://weixin.sogou.com" + link
        out.append({
            "title": strip_tags(m.group(2)),
            "site": strip_tags(acct.group(1)) if acct else "",
            "published": time.strftime("%Y-%m-%d", time.localtime(int(t.group(1)))) if t else "",
            "snippet": strip_tags(info.group(1)) if info else "",
            "url": link,
        })
    return out


def parse_web(html: str) -> list[dict[str, str]]:
    out = []
    for m in re.finditer(r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        link, title = m.group(1), strip_tags(m.group(2))
        # 摘要紧跟标题后的段落
        tail = html[m.end(): m.end() + 1200]
        info = re.search(r'<p[^>]*class="star-wiki"[^>]*>(.*?)</p>|<div[^>]*class="[^"]*(?:text-layout|fz-mid)[^"]*"[^>]*>(.*?)</div>', tail, re.S)
        snip = strip_tags(info.group(1) or info.group(2)) if info else strip_tags(tail)[:160]
        cite = re.search(r'class="citeurl"[^>]*>(.*?)</span>', tail, re.S)
        out.append({
            "title": title, "site": strip_tags(cite.group(1)) if cite else "",
            "published": "", "snippet": snip, "url": link,
        })
    return out


CHANNELS = {
    "sogou-wechat": ("https://weixin.sogou.com/weixin?type=2&query=", parse_wechat),
    "sogou-web": ("https://www.sogou.com/web?query=", parse_web),
}


def main(argv: list[str]) -> int:
    channels = ["sogou-wechat", "sogou-web"]
    if "--channels" in argv:
        channels = argv[argv.index("--channels") + 1].split(",")
    counties: list[tuple[str, str]] = []
    if "--counties" in argv:
        codes = argv[argv.index("--counties") + 1].split(",")
        import sqlite3
        con = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
        nm = {r[0]: r[1] for r in con.execute(
            "select region_code, name from region where level='county'")}
        counties = [(c, nm.get(c, c)) for c in codes if c]
    else:
        with GAPS.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        start = int(argv[argv.index("--from-code") + 1]) if "--from-code" in argv else 0
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 10
        counties = [(r["county_code"], r["county_name"]) for r in rows[start:start + limit]]

    print(f"目标 {len(counties)} 个县，通道 {channels}")
    leads: list[dict[str, str]] = []
    failed: list[str] = []
    blocked_streak = 0
    for i, (code, name) in enumerate(counties, 1):
        if blocked_streak >= MAX_CONSECUTIVE_BLOCK:
            print(f"  连续 {blocked_streak} 次反爬，中止本轮（已处理 {i-1} 个县）。"
                  f"隔一段时间再用 --from-code {i-1} 续跑")
            break
        queries = [f"{name} 片区 乡村振兴"]
        for ch in channels:
            for qq in queries:
                base, parser = CHANNELS[ch]
                try:
                    html = fetch(base + urllib.parse.quote(qq),
                                 referer="https://www.sogou.com/")
                except Exception as e:                     # noqa: BLE001
                    failed.append(f"{code} {ch} {e}")
                    continue
                if is_blocked(html):
                    print(f"  [{i}/{len(counties)}] {code} {name} {ch}: 命中反爬，冷却 {BLOCK_SLEEP}s")
                    blocked_streak += 1
                    time.sleep(BLOCK_SLEEP)
                    try:
                        html = fetch(base + urllib.parse.quote(qq),
                                     referer="https://www.sogou.com/")
                    except Exception:                      # noqa: BLE001
                        continue
                    if is_blocked(html):
                        continue
                blocked_streak = 0
                got = parser(html)
                hit = 0
                for r in got:
                    text = r["title"] + " " + r["snippet"]
                    # 必须出现**全名**（含县/区/市后缀）：只用前两字会被「灵珠山街道」这类误命中
                    if name not in text:
                        continue
                    if not any(t in text for t in TERMS):
                        continue
                    if any(x in text for x in EXCLUDE):
                        continue
                    leads.append({"county_code": code, "county_name": name,
                                  "channel": ch, "query": qq, **r})
                    hit += 1
                print(f"  [{i}/{len(counties)}] {code} {name} {ch}: 抓 {len(got)} 条，命中 {hit}")
                time.sleep(SLEEP)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"media-leads-{date.today().isoformat()}.csv"
    merged: dict[tuple[str, str], dict[str, str]] = {}
    if out.exists():
        with out.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("title"):
                    merged[(r["county_code"], r["title"])] = r
    for r in leads:
        merged[(r["county_code"], r["title"])] = r
    if merged:
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["county_code", "county_name", "channel",
                                              "query", "title", "site", "published",
                                              "snippet", "url"])
            w.writeheader()
            w.writerows(merged.values())
    covered = len({r["county_code"] for r in merged.values()})
    print(f"\n本次命中 {len(leads)} 条；累计 {len(merged)} 条 / 覆盖 {covered} 个县"
          f" -> {out.relative_to(ROOT)}")
    if failed:
        print(f"失败 {len(failed)} 次（前 3）：{failed[:3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
