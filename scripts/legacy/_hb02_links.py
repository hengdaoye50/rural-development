# -*- coding: utf-8 -*-
import re, urllib.request, sys
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
      "Accept-Encoding": "identity", "Connection": "close"}
for u in sys.argv[1:]:
    try:
        h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        print(u, "FAIL", e); continue
    print("====", u, len(h))
    for m in re.findall(r"<option[^>]*value=[\"']([^\"']+)[\"'][^>]*>([^<]+)</option>", h):
        if "gov.cn" in m[0]:
            print("  ", m[1].strip(), m[0])
