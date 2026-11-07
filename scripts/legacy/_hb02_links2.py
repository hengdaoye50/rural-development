# -*- coding: utf-8 -*-
"""通用：抓页面并打印含关键词的链接 / 表单。用法: python _hb02_links2.py <url> [kw1,kw2]"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
      "Accept": "text/html,*/*;q=0.8", "Accept-Encoding": "identity", "Connection": "close"}

url = sys.argv[1]
kws = sys.argv[2].split(",") if len(sys.argv) > 2 else ["公开", "文件", "政策", "通知", "公告", "规划", "片区", "样板", "农村", "农业"]
try:
    h = urllib.request.urlopen(urllib.request.Request(url, headers=HD), timeout=30).read().decode("utf-8", "replace")
except Exception as e:
    print("FAIL", e)
    sys.exit(1)
print("len", len(h))
print("--- forms ---")
for f in re.findall(r"(?s)<form[^>]*>.{0,400}?</form>", h)[:8]:
    print(re.sub(r"\s+", " ", f)[:300])
    print("  --")
print("--- links ---")
seen = set()
for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>([^<]{2,40})</a>", h):
    u, t = m.group(1), m.group(2).strip()
    if any(k in t for k in kws) and u not in seen:
        seen.add(u)
        print("  %s  ->  %s" % (t, u))
print("--- search urls ---")
for u in sorted(set(re.findall(r"[\"']([^\"']{0,120}(?:search|sousuo|jsearch)[^\"']{0,120})[\"']", h, re.I)))[:10]:
    print("  ", u)
