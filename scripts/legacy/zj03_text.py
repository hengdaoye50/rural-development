import re
import sys

import requests

requests.packages.urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

url = sys.argv[1]
r = requests.get(url, headers=H, timeout=45, verify=False)
r.encoding = r.apparent_encoding or "utf-8"
html = r.text
body = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
body = re.sub(r"(?s)<[^>]+>", "\n", body)
body = re.sub(r"\n{2,}", "\n", body)
lines = [x.strip() for x in body.splitlines() if x.strip()]
print("\n".join(lines))
