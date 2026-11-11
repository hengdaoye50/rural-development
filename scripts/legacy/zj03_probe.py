import re
import sys

import requests

requests.packages.urllib3.disable_warnings()
sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

for u in sys.argv[1:]:
    try:
        r = requests.get(u, headers=H, timeout=45, verify=False)
        r.encoding = r.apparent_encoding or "utf-8"
        print("==", u, r.status_code, len(r.text))
        for m in re.finditer(r'href="([^"]+\.(?:pdf|PDF|doc|docx|xls|xlsx))"', r.text):
            print("  ATT:", m.group(1))
    except Exception as e:  # noqa: BLE001
        print("ERR", u, repr(e))
