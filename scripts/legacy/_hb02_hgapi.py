# -*- coding: utf-8 -*-
"""探测黄冈平台栏目页的数据接口 / 内联数据。"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept-Encoding": "identity", "Connection": "close"}
u = sys.argv[1]
h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=30).read().decode("utf-8", "replace")
print("len", len(h))
print("--- api/json hints ---")
for m in sorted(set(re.findall(r"[\"']([^\"']{0,160}(?:/api/|api/|\.json|getList|columnList)[^\"']{0,160})[\"']", h)))[:20]:
    print("  ", m)
print("--- inline article ids ---")
ids = sorted(set(re.findall(r"/content/article/(\d+)", h)))
print("  ", ids[:20], "count", len(ids))
print("--- titles near ids ---")
for m in re.finditer(r'>([^<>]{6,60})</a>', h):
    t = m.group(1).strip()
    if any(k in t for k in ("片区", "样板", "示范", "和美", "乡村振兴", "农村", "规划", "报告")):
        print("  ", t)
