import sys

import requests

requests.packages.urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

url, out = sys.argv[1], sys.argv[2]
r = requests.get(url, headers=H, timeout=120, verify=False)
print(r.status_code, len(r.content), r.headers.get("content-type"))
open(out, "wb").write(r.content)
print("saved", out)
