import re, sys, ssl, urllib.request, gzip, io

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def get(u):
    req = urllib.request.Request(u, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Encoding": "gzip",
    })
    r = urllib.request.urlopen(req, timeout=40, context=ctx)
    raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", "replace")


if __name__ == "__main__":
    t = get(sys.argv[1])
    print("LEN", len(t))
    for p in ["dataproxy", "jpage", "columnid", "getXML", "list.json"]:
        for m in re.finditer(re.escape(p), t):
            s = max(0, m.start() - 250)
            print("===", p, "===")
            print(t[s:m.start() + 350].replace("\n", " "))
            break
