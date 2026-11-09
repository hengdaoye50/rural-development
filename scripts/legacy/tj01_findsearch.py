import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_probe import fetch  # noqa: E402

url = sys.argv[1]
kw = sys.argv[2] if len(sys.argv) > 2 else "search"
h = fetch(url)
seen = set()
for m in re.finditer(r'(?:href|action|src)\s*=\s*["\']([^"\']+)["\']', h, re.I):
    v = m.group(1)
    if kw.lower() in v.lower() and v not in seen:
        seen.add(v)
        print(v)
for m in re.finditer(r'(?i)["\'](https?://[^"\']*(?:search|jsearch|was5)[^"\']*)["\']', h):
    if m.group(1) not in seen:
        seen.add(m.group(1))
        print(m.group(1))
