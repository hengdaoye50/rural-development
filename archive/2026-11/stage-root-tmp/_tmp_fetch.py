import sys, urllib.request, gzip, io, re, os, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
    data = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        data = gzip.decompress(data)
    enc = "utf-8"
    ct = r.headers.get("Content-Type", "") or ""
    m = re.search(r"charset=([\w-]+)", ct, re.I)
    if m:
        enc = m.group(1)
    else:
        m = re.search(rb'charset=["\']?([\w-]+)', data[:3000], re.I)
        if m:
            enc = m.group(1).decode("ascii", "ignore")
    try:
        return data.decode(enc, "replace")
    except LookupError:
        return data.decode("utf-8", "replace")


def text_of(html):
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return re.sub(r"[ \t\r\f\v]+", " ", html)


if __name__ == "__main__":
    url = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "text"
    h = fetch(url)
    if mode == "text":
        t = text_of(h)
        t = re.sub(r"\n\s*\n+", "\n", t)
        print(t)
    elif mode == "links":
        kw = sys.argv[3] if len(sys.argv) > 3 else ""
        for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
            href, label = m.group(1), re.sub(r"(?s)<[^>]+>", "", m.group(2)).strip()
            if kw and kw not in label:
                continue
            print(label[:70], "|", href)
    else:
        print(h)
