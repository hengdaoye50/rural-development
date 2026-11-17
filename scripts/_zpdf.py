import sys
import urllib.request

from pypdf import PdfReader

for u in sys.argv[1:]:
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=90).read()
    out = "data/stage/_tmp.pdf"
    with open(out, "wb") as f:
        f.write(raw)
    print("=" * 30, u, len(raw))
    r = PdfReader(out)
    print("pages", len(r.pages))
    txt = "\n".join((p.extract_text() or "") for p in r.pages)
    print("chars", len(txt))
    print(txt[:3000])
