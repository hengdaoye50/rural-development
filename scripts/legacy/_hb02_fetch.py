# -*- coding: utf-8 -*-
"""HB02 辅助抓取：取政府网正文，输出 markdown 片段到 _hb02_out/。"""
import os, re, sys, json, hashlib, urllib.request

OUT = os.path.join("scripts", "legacy", "_hb02_out")
os.makedirs(OUT, exist_ok=True)
HD = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def get(url, timeout=45, referer=None):
    h = dict(HD)
    h["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    h["Accept-Encoding"] = "identity"
    h["Connection"] = "close"
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    raw = urllib.request.urlopen(req, timeout=timeout).read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_tags(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</(p|div|tr|h[1-6]|li)>", "\n", html)
    html = re.sub(r"(?i)</t[dh]>", " | ", html)
    html = re.sub(r"<[^>]+>", "", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&ldquo;", "“").replace("&rdquo;", "”")
    lines = [re.sub(r"[ \t\u3000]+", " ", l).strip() for l in html.split("\n")]
    out = []
    for l in lines:
        if not l:
            if out and out[-1] != "":
                out.append("")
            continue
        if l in ("|",) or set(l) <= set("| "):
            continue
        out.append(l)
    return "\n".join(out).strip()


def body(html):
    """取正文：优先常见正文容器 id/class。"""
    cands = []
    for pat in (r'(?is)<div[^>]+id="zoom"[^>]*>(.*?)</div>\s*(?:<div|<script|<!--)',
                r'(?is)<div[^>]+class="[^"]*(?:TRS_Editor|article-content|artical|content|zwxl|xl_con|view|detail)[^"]*"[^>]*>(.*?)</div>',
                r'(?is)<td[^>]+class="[^"]*(?:content|txt)[^"]*"[^>]*>(.*?)</td>'):
        cands += re.findall(pat, html)
    best = ""
    for c in cands:
        t = strip_tags(c)
        if len(t) > len(best):
            best = t
    if len(best) < 120:
        # fallback: whole page, cut between 当前位置 and 扫一扫
        t = strip_tags(html)
        m = re.search(r"(?s)当前位置[:：].*?\n", t)
        if m:
            t = t[m.end():]
        t = re.split(r"扫一扫在手机上查看当前页面", t)[0]
        best = t.strip()
    return best


def count_chars(t):
    return len(re.sub(r"\s", "", t))


if __name__ == "__main__":
    for url in sys.argv[1:]:
        key = hashlib.md5(url.encode()).hexdigest()[:10]
        try:
            html = get(url)
        except Exception as e:
            print("FAIL", url, e)
            continue
        b = body(html)
        path = os.path.join(OUT, key + ".md")
        open(path, "w", encoding="utf-8").write(url + "\n\n" + b)
        print("%s\t%d\t%s" % (key, count_chars(b), url))
