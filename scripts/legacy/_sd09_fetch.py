"""Fetch gov.cn page bodies (stdlib only) and append near-complete jsonl records.

Usage: python _sd09_fetch.py meta.json
meta.json = list of records WITHOUT full_text; each must have "url".
Script fills full_text from the fetched page body, then appends to the batch jsonl
with url-level dedupe.
"""
import json, sys, os, io, re, ssl, urllib.request
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

DROP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "form", "iframe", "select"}
BLOCK_TAGS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "section", "article"}
HEAD_TAGS = {"h1", "h2", "h3", "h4", "h5"}

CAPTURE_HINTS = ("zoom", "trs_editor", "ivs_content", "article-content", "article_content",
                 "content", "con", "zw", "text", "view", "detail", "main-content", "article",
                 "custom_unionstyle", "ucap-content", "bt_content", "show_content", "c_body")

BOILER = ("分享到", "关闭窗口", "打印", "收藏", "扫一扫", "网站地图", "主办", "承办",
          "ICP备", "公网安备", "网站标识码", "返回顶部", "上一篇", "下一篇", "相关推荐",
          "版权所有", "Copyright", "字号", "朗读", "无障碍", "长者", "手机版",
          "国内政府网站", "省内政府网站", "市内政府网站", "县内政府网站", "区县政府网站",
          "智能问答", "政务微博", "政务微信", "爱山东APP", "纠正文", "Word版下载",
          "PDF版下载", "数据开放", "政民互动", "政务服务", "走进沂水", "走进")


def _attr_hit(attrs):
    for k, v in attrs:
        if k in ("class", "id") and v:
            low = v.lower()
            if any(h in low for h in CAPTURE_HINTS):
                return True
    return False


class BodyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.cap_depth = None
        self.buf = []
        self.best = ""
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_TAGS:
            self.skip += 1
        if tag == "br":
            if self.cap_depth is not None:
                self.buf.append("\n")
            return
        if self.cap_depth is None:
            if _attr_hit(attrs):
                self.cap_depth = self.depth
                self.buf = []
        elif tag in BLOCK_TAGS:
            self.buf.append("\n\n")
            if tag in HEAD_TAGS:
                self.buf.append("## ")
        elif tag in ("td", "th"):
            self.buf.append(" | ")
        self.depth += 1

    def handle_endtag(self, tag):
        if tag in DROP_TAGS and self.skip:
            self.skip -= 1
        self.depth -= 1
        if self.cap_depth is not None and self.depth <= self.cap_depth and tag not in ("br", "img"):
            txt = _tidy("".join(self.buf))
            if len(txt) > len(self.best):
                self.best = txt
            self.cap_depth = None
            self.buf = []

    def handle_data(self, data):
        if self.skip or self.cap_depth is None:
            return
        self.buf.append(data)

    def close(self):
        super().close()
        if self.cap_depth is not None:
            txt = _tidy("".join(self.buf))
            if len(txt) > len(self.best):
                self.best = txt
            self.cap_depth = None


def _tidy(s):
    lines = []
    for ln in s.split("\n"):
        ln = ln.strip()
        ln = re.sub(r"[ \t\u3000]+", " ", ln)
        lines.append(ln)
    out = []
    for ln in lines:
        if not ln:
            out.append("")
            continue
        if len(ln) < 120 and any(b in ln for b in BOILER):
            continue
        out.append(ln)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt


FALLBACK_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def extract(html):
    p = BodyParser()
    p.feed(FALLBACK_TAG_RE.sub("", html))
    p.close()
    if len(p.best) >= 150:
        return p.best
    # fallback: whole body, tags stripped
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    body = m.group(1) if m else html
    body = FALLBACK_TAG_RE.sub("", body)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</(p|div|tr|li|h[1-5])>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    body = body.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return _tidy(body)


def pdf_text(raw):
    import tempfile
    from pypdf import PdfReader
    fd, tmp = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.write(raw)
        r = PdfReader(tmp)
        pages = []
        for pg in r.pages:
            try:
                pages.append(pg.extract_text() or "")
            except Exception:
                pages.append("")
        txt = "\n".join(pages)
        txt = re.sub(r"[ \t\u3000]+", " ", txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        return txt.strip()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "zh-CN,zh;q=0.9"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        raw = r.read()
        ctype = r.headers.get("Content-Type", "") or ""
    if raw[:4] == b"%PDF" or "pdf" in ctype.lower():
        return ("__PDF__", pdf_text(raw))
    for enc in ("utf-8", "gb18030", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def main():
    with io.open(sys.argv[1], encoding="utf-8") as f:
        recs = json.load(f)

    existing = set()
    if os.path.exists(TARGET):
        with io.open(TARGET, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing.add(json.loads(line).get("url", ""))

    added = 0
    with io.open(TARGET, "a", encoding="utf-8", newline="\n") as out:
        for rec in recs:
            url = rec["url"]
            if url in existing:
                print("SKIP dup:", url)
                continue
            try:
                got = fetch(url)
            except Exception as e:
                print("FETCH FAIL", url, type(e).__name__, e)
                continue
            if isinstance(got, tuple):
                md = got[1]
            else:
                md = extract(got)
            if len(md) < 150:
                print("SHORT (%d chars), NOT written: %s" % (len(md), url))
                continue
            rec["full_text"] = md
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            existing.add(url)
            added += 1
            print("ADDED %5d chars | %s | areas=%s" % (
                len(re.sub(r"\s", "", md)), rec.get("title", "")[:44],
                [a["area_id"] for a in rec.get("areas", [])]))
    print("total added:", added)


if __name__ == "__main__":
    main()
