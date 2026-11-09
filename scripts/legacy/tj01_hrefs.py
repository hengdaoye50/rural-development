import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_probe import fetch  # noqa: E402

url = sys.argv[1]
pat = sys.argv[2] if len(sys.argv) > 2 else r"index|page|next"
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 40
h = fetch(url)
print(f"# len={len(h)}")
seen = set()
n = 0
for m in re.finditer(r'href=["\']([^"\']+)["\']', h):
    v = m.group(1)
    if re.search(pat, v, re.I) and v not in seen:
        seen.add(v)
        print(v)
        n += 1
        if n >= limit:
            break
