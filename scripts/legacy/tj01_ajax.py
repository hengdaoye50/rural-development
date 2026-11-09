import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_probe import fetch  # noqa: E402

url = sys.argv[1]
h = fetch(url)
pats = sys.argv[2:] or [r"url\s*:\s*['\"]([^'\"]+)", r"\$\.(?:get|post|ajax)"]
for p in pats:
    for m in re.finditer(p, h, re.I):
        print("HIT", m.group(0)[:200])
for m in re.finditer(r"(?i)([A-Za-z0-9_./?=&%-]*(?:json|api|search|list|query)[A-Za-z0-9_./?=&%-]*)", h):
    v = m.group(1)
    if len(v) > 8 and ("http" in v or v.startswith("/") or v.startswith("./") or v.startswith("..")):
        print("URL", v)
