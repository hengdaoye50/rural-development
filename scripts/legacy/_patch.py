import io,re,os
p = r"data/stage/batches/_sd09_fetch.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
"""def fetch(url):""",
'''def pdf_text(raw):
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
        txt = "\\n".join(pages)
        txt = re.sub(r"[ \\t\\u3000]+", " ", txt)
        txt = re.sub(r"\\n{3,}", "\\n\\n", txt)
        return txt.strip()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def fetch(url):''')
s = s.replace(
"""        raw = r.read()
        ctype = r.headers.get("Content-Type", "") or ""
""",
"""        raw = r.read()
        ctype = r.headers.get("Content-Type", "") or ""
    if raw[:4] == b"%PDF" or "pdf" in ctype.lower():
        return pdf_text(raw)
""")
io.open(p,"w",encoding="utf-8",newline="\n").write(s)
print("patched")
