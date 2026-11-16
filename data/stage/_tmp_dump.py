import re, sys
import _tmp_fetch as f

for url in sys.argv[1:]:
    print("=== ", url)
    try:
        h = f.fetch(url, timeout=20)
    except Exception as e:
        print("  ERR", type(e).__name__, str(e)[:80])
        continue
    print("  LEN", len(h))
    if len(h) < 400:
        print("  RAW:", h[:400])
        continue
    n = 0
    for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        lab = re.sub(r'\s+', ' ', re.sub(r'(?s)<[^>]+>', '', m.group(2))).strip()
        if not lab:
            continue
        n += 1
        if n <= 25:
            print("   ", lab[:45], "|", m.group(1)[:70])
    print("  total anchors", n)
