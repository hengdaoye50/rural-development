# -*- coding: utf-8 -*-
"""探测黄冈市政府网站群检索 API（覆盖团风县、英山县等县市子站）。"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
      "Accept-Encoding": "identity", "Connection": "close"}

u = ("https://www.hg.gov.cn/site/search/6799394?siteId=6792758&platformCode=hg-xq"
     "&keywords=%E6%A0%B7%E6%9D%BF%E5%B8%A6")
h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=30).read().decode("utf-8", "replace")
print("len", len(h))
print("--- urls ---")
for m in sorted(set(re.findall(r"https?://[^\"'\s<>]{0,160}", h))):
    if "api" in m or "search" in m or "es." in m:
        print(m)
print("--- inline api hints ---")
for m in sorted(set(re.findall(r"[\"'/][^\"'\s<>]{0,80}(?:searchApp|searchApi|/api/|esSearch|solr)[^\"'\s<>]{0,80}", h))):
    print(m)
print("--- script srcs ---")
for m in re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", h):
    print(m)
print("--- head snippet ---")
print(h[:1200])
