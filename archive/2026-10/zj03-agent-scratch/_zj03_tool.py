# -*- coding: utf-8 -*-
"""ZJ03 采集辅助：纯标准库抓取 + HTML 转文本/链接列表。
用法:
  python _zj03_tool.py title <url>
  python _zj03_tool.py links <url> [kw]        # 列出链接（可按关键词过滤）
  python _zj03_tool.py grep  <url> kw1 kw2 ... # 打印命中关键词的段落
  python _zj03_tool.py text  <url> [maxchars]  # 打印正文纯文本
  python _zj03_tool.py save  <url> <outfile>   # 保存正文文本
"""
import sys, re, gzip, io, os, urllib.request, urllib.error, ssl

sys.stdout.reconfigure(encoding="utf-8")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read()
        enc = r.headers.get("Content-Encoding", "")
        if "gzip" in enc:
            raw = gzip.decompress(raw)
        ctype = r.headers.get("Content-Type", "")
        m = re.search(r"charset=([\w-]+)", ctype, re.I)
        cands = []
        if m:
            cands.append(m.group(1))
        head = raw[:3000].decode("latin-1", "ignore")
        m2 = re.search(r'charset=["\']?([\w-]+)', head, re.I)
        if m2:
            cands.append(m2.group(1))
        cands += ["utf-8", "gb18030"]
        for c in cands:
            try:
                return raw.decode(c, "strict")
            except Exception:
                continue
        return raw.decode("utf-8", "ignore")


def strip(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|tr|li|h[1-6]|td|table|section)>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&ldquo;", "“"), ("&rdquo;", "”"),
                 ("&mdash;", "—"), ("&middot;", "·")]:
        html = html.replace(a, b)
    html = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), html)
    lines = [re.sub(r"[ \t\u3000]+", " ", l).strip() for l in html.split("\n")]
    return "\n".join([l for l in lines if l])


def links(html, base):
    out = []
    for m in re.finditer(r'(?is)<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html):
        href = m.group(1)
        txt = strip(m.group(2)).replace("\n", " ").strip()
        if href.startswith("javascript") or href.startswith("#"):
            continue
        out.append((href, txt))
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, url = sys.argv[1], sys.argv[2]
    html = fetch(url)
    if cmd == "links":
        kws = sys.argv[3:]
        seen = set()
        for href, txt in links(html, url):
            if kws and not any(k in txt or k in href for k in kws):
                continue
            key = (href, txt)
            if key in seen:
                continue
            seen.add(key)
            print(f"{href}\t{txt}")
    elif cmd == "grep":
        kws = sys.argv[3:] or ["片区"]
        txt = strip(html)
        ttl = re.search(r"(?is)<title>(.*?)</title>", html)
        print("TITLE:", strip(ttl.group(1)) if ttl else "")
        paras = [p for p in txt.split("\n") if any(k in p for k in kws)]
        for p in paras[:120]:
            print("  *", p[:600])
        print(f"[hits={len(paras)}]")
    elif cmd == "text":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 100000
        txt = strip(html)
        print(txt[:n])
    elif cmd == "title":
        ttl = re.search(r"(?is)<title>(.*?)</title>", html)
        print(strip(ttl.group(1)) if ttl else "(no title)")
    elif cmd == "save":
        open(sys.argv[3], "w", encoding="utf-8").write(strip(html))
        print("saved", sys.argv[3], len(strip(html)))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
