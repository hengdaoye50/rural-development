"""Extract readable main text from a gov HTML page."""
import sys, re, html
from _tmp_web import get, dec

def to_md(url, save=None):
    st, raw = get(url)
    t = dec(raw)
    # drop scripts/styles
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
    title = ''
    m = re.search(r'<title[^>]*>(.*?)</title>', t, re.S | re.I)
    if m:
        title = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    # paragraphs / divs with text
    body = t
    m2 = re.search(r'(?:id=["\']?zoom["\']?|class=["\'][^"\']*(?:TRS_Editor|article|content|detail|zoom|view)[^"\']*["\'])', body, re.I)
    seg = body
    t = re.sub(r'<(p|br|div|h1|h2|h3|li|tr)[^>]*>', '\n', seg, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    lines = [ln.strip() for ln in t.split('\n')]
    out = []
    for ln in lines:
        if not ln:
            continue
        out.append(ln)
    txt = '\n'.join(out)
    if save:
        with open(save, 'w', encoding='utf-8') as f:
            f.write(txt)
    return title, txt

if __name__ == '__main__':
    url = sys.argv[1]
    save = sys.argv[2] if len(sys.argv) > 2 else None
    title, txt = to_md(url, save)
    print('TITLE:', title)
    print('LEN:', len(txt))
    print(txt[:5000] if len(sys.argv) < 4 else txt)
