import re, sys
from _tmp_probe import get

t = get(sys.argv[1])
pat = sys.argv[2] if len(sys.argv) > 2 else "col"
seen = set()
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', t, re.S):
    txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    txt = re.sub(r"\s+", " ", txt)
    h = m.group(1)
    if txt and pat in h and txt not in seen and len(txt) < 40:
        seen.add(txt)
        print(txt, "||", h[:100])
