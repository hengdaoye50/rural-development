import sys, io, re, os, urllib.request, pypdf

sys.stdout.reconfigure(encoding='utf-8')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.headers.get('Content-Type', '')


def decode(raw, ct):
    m = re.search(r'charset=([\w-]+)', ct or '', re.I)
    cands = []
    if m:
        cands.append(m.group(1))
    m2 = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    if m2:
        cands.append(m2.group(1).decode('ascii', 'ignore'))
    cands += ['utf-8', 'gb18030']
    for c in cands:
        try:
            return raw.decode(c)
        except Exception:
            continue
    return raw.decode('utf-8', 'ignore')


BOXES = [
    r'<div[^>]*class="[^"]*TRS_Editor[^"]*"[^>]*>',
    r'<div[^>]*id="zoom"[^>]*>',
    r'<div[^>]*class="[^"]*(?:article|content|conTxt|view|detail|txt)[^"]*"[^>]*>',
    r'<td[^>]*class="[^"]*(?:content|txt)[^"]*"[^>]*>',
]


def to_md(html):
    html = re.sub(r'(?is)<(script|style|noscript).*?</\1>', ' ', html)
    html = re.sub(r'(?i)<br\s*/?>', '\n', html)
    html = re.sub(r'(?i)</(p|div|tr|h1|h2|h3|h4|li|td)>', '\n', html)
    html = re.sub(r'&nbsp;?', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&lt;', '<', html)
    html = re.sub(r'&gt;', '>', html)
    html = re.sub(r'&quot;', '"', html)
    html = re.sub(r'(?s)<[^>]+>', '', html)
    lines = [l.strip() for l in html.split('\n')]
    lines = [l for l in lines if l]
    return '\n'.join(lines)


def body(html):
    for pat in BOXES:
        for m in re.finditer(pat, html, re.I):
            seg = html[m.end():]
            nxt = re.search(r'(?is)<div[^>]*class="[^"]*TRS_Editor', seg)
            if nxt:
                seg = seg[:nxt.start()]
            txt = to_md(seg)
            if len(txt) > 200:
                return txt
    return to_md(html)


def pdf_text(raw):
    rd = pypdf.PdfReader(io.BytesIO(raw))
    return '\n'.join('=== page %d ===\n%s' % (i, p.extract_text() or '') for i, p in enumerate(rd.pages, 1))


if __name__ == '__main__':
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else ''
    raw, ct = fetch(url)
    sys.stderr.write('#CT %s #BYTES %d\n' % (ct, len(raw)))
    if raw[:4] == b'%PDF' or 'pdf' in (ct or '').lower():
        txt = pdf_text(raw)
    else:
        txt = body(decode(raw, ct))
    if out:
        open(out, 'w', encoding='utf-8', newline='\n').write(txt)
        sys.stderr.write('#WROTE %s chars=%d\n' % (out, len(txt)))
    else:
        print(txt)
