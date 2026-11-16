import sys, os, io, re, urllib.request, gzip, ssl
import _tmp_fetch as f

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gzbg")
os.makedirs(OUT, exist_ok=True)


def pdf_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": f.UA})
    r = urllib.request.urlopen(req, timeout=60, context=ctx)
    data = r.read()
    from pypdf import PdfReader
    rd = PdfReader(io.BytesIO(data))
    parts = []
    for p in rd.pages:
        parts.append(p.extract_text() or "")
    return "\n".join(parts), len(data)


if __name__ == "__main__":
    tag, url = sys.argv[1], sys.argv[2]
    try:
        t, n = pdf_text(url)
    except Exception as e:
        print("PDFERR", tag, type(e).__name__, str(e)[:100])
        sys.exit(1)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    p = os.path.join(OUT, tag + ".txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("URL: " + url + "\n")
        fh.write(t)
    print(tag, "pdfbytes=", n, "chars=", len(t), "片区=", t.count("片区"), "->", p)
