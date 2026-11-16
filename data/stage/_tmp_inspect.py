import re, sys
import _tmp_fetch as f

url = sys.argv[1]
h = f.fetch(url)
print("LEN", len(h))
for m in re.finditer(r'(?i)(href|src)\s*=\s*["\']([^"\']+)["\']', h):
    if any(k in m.group(2).lower() for k in ("pdf", "doc", ".js?", "content", "upload")):
        print(m.group(1), m.group(2))
print("---TAIL---")
print(h[-1200:])
