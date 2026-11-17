import re
import sys
import urllib.request

sys.path.insert(0, "scripts")
from _zjfetch import get  # noqa: E402

u = sys.argv[1]
h = get(u)
print("HTML LEN", len(h))
for m in re.finditer(r'(?:href|src)="([^"]+)"', h):
    v = m.group(1)
    if re.search(r"\.(pdf|doc|docx|wps|ofd|html?|txt)$", v, re.I) or "attach" in v.lower() or "download" in v.lower():
        print("LINK", v[:220])
i = h.find("绍政发")
print(h[max(0, i - 300): i + 3000])
