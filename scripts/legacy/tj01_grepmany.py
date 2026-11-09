import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_grep import text_of  # noqa: E402
from tj01_probe import fetch  # noqa: E402

kws = sys.argv[1].split(",")
win = int(sys.argv[2]) if len(sys.argv) > 2 else 90
for url in sys.argv[3:]:
    try:
        body = text_of(fetch(url))
    except Exception as exc:  # noqa: BLE001
        print(f"# {url} ERR {exc}")
        continue
    print(f"# {url} chars={len(body)}")
    hits = 0
    for kw in kws:
        for m in re.finditer(kw, body):
            s = max(0, m.start() - win)
            print(f"  [{kw}] ...{body[s:m.end() + win].replace(chr(10), ' ')}...")
            hits += 1
            if hits >= 12:
                break
        if hits >= 12:
            break
    if not hits:
        print("  (no hit)")
