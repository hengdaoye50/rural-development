# -*- coding: utf-8 -*-
"""黄冈平台 label API 取栏目文章列表。用法: python _hb02_hglabel.py <siteId> <organId> <catId> <pageSize> [kw]"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept-Encoding": "identity", "Connection": "close"}
site, organ, cat = sys.argv[1], sys.argv[2], sys.argv[3]
size = sys.argv[4] if len(sys.argv) > 4 else "50"
kws = sys.argv[5].split(",") if len(sys.argv) > 5 else None
u = ("https://www.chinays.gov.cn/zwgk/site/label/8888?labelName=publicInfoList&siteId=%s&organId=%s"
     "&pageSize=%s&catId=%s&type=4&length=200&dateFormat=yyyy-MM-dd&file=/c2/xxgk/publicInfoList_newest_zc01"
     % (site, organ, cat, size))
h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=40).read().decode("utf-8", "replace")
print("len", len(h))
seen = set()
for m in re.finditer(r'<a[^>]+href="([^"]*?/content/article/\d+[^"]*)"[^>]*(?:title="([^"]*)")?[^>]*>(.*?)</a>', h, re.S):
    u2, ttl, inner = m.group(1), m.group(2), re.sub(r"<[^>]+>", "", m.group(3))
    t = (ttl or inner).strip()
    if not t or u2 in seen:
        continue
    seen.add(u2)
    if kws and not any(k in t for k in kws):
        continue
    print("%s | https://www.chinays.gov.cn%s" % (t[:60], u2 if u2.startswith("/") else u2))
print("total links", len(seen))
