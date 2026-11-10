import sys, os, urllib.request, ssl, gzip
from _tmp_probe import get  # noqa

def dl(u, out):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(u, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    })
    r = urllib.request.urlopen(req, timeout=120, context=ctx)
    raw = r.read()
    if r.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    open(out, "wb").write(raw)
    print("OK", out, len(raw), r.headers.get("Content-Type"))

if __name__ == "__main__":
    dl(sys.argv[1], sys.argv[2])
