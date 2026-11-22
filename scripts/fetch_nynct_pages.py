# -*- coding: utf-8 -*-
"""抓取浙江省农业农村厅 21 个页面并保存正文（只读采集）。

输出：data/raw/ZJ/2026-nynct/{idx:02d}.md 与 pages.csv（idx,url,title,chars,片区数）
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "ZJ" / "2026-nynct"
URLS = [
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_8b82fe4a65ec4bb0941f089935cbd7dd.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_f811399b2481460ca2abd083f230bf94.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_d7e47da4107a4d16a7212be7a907c1df.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_597eaeb723e84f8f9fcf2716725a5020.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_e12fe567635647e5a166472bb0fc21b6.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_935a679eb0a744ff9a066ca489bafc69.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_8672781df5894a4c8a79d8456b6a1939.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_67a64ed3e6ae4d8f8b4dafbd1a4e0ca4.html",
    "https://nynct.zj.gov.cn/col/col1589296/art/2026/art_0ed18756abe9482eac6a1d4c2b38539d.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_e0afac55092542fe9bf2f1c5577160c2.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_162c32bf85594c6fbf7a8bb5d6906be1.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_4824711882be4ff4bef26fcf134aaccc.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_bcbe5160ba7f4347abff9d553eeb2b89.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_6cbdf6da1e0e472691f27cb58fa7458a.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_c36797fa0f194f16bd1f0cb23922d6c5.html",
    "https://nynct.zj.gov.cn/col/col1589296/art/2026/art_39e3fa05af064fdfb55010273aa203f1.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_9c049f521f2a47ae87bf8fa290677c27.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_23cb7b5b44d4423c9418d01cc422a906.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_6afb746c89764998ad571c50a8355513.html",
    "https://nynct.zj.gov.cn/col/col1589296/art/2026/art_ed9ad0228ce2457a96563b91d03e8936.html",
    "https://nynct.zj.gov.cn/col/col1229746526/art/2026/art_f08f42cd73c64eed99a1c41e1601ba17.html",
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, url in enumerate(URLS, 1):
        try:
            r = requests.get(url, headers=UA, timeout=40)
            r.encoding = r.apparent_encoding or "utf-8"
            html = r.text
        except Exception as e:  # noqa: BLE001
            print(f"{i:02d} ERR {e}")
            rows.append({"idx": i, "url": url, "title": "", "chars": 0, "片区数": 0})
            continue
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        title = (title.group(1).strip() if title else "")
        body = TAG.sub("", html)
        body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
        body = re.sub(r"</p>", "\n", body, flags=re.I)
        body = re.sub(r"<[^>]+>", "", body)
        body = re.sub(r"[ \t\u3000]+", " ", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        (OUT / f"{i:02d}.md").write_text(body, encoding="utf-8")
        n = body.count("片区")
        rows.append({"idx": i, "url": url, "title": title, "chars": len(body), "片区数": n})
        print(f"{i:02d} chars={len(body):5d} 片区={n:3d}  {title[:50]}")
    with (OUT / "pages.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["idx", "url", "title", "chars", "片区数"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
