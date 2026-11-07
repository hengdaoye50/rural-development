# -*- coding: utf-8 -*-
"""测试荆州市政府网站群各县市 search.html 是否存在。"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept-Encoding": "identity", "Connection": "close"}
kw = "%E6%A0%B7%E6%9D%BF%E5%B8%A6"
for slug in ["songzishi", "hbsz", "szs", "jingzhoushi", "sz"]:
    u = "https://www.jingzhou.gov.cn/site/%s/search.html?searchWord=%s" % (slug, kw)
    try:
        h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=25).read().decode("utf-8", "replace")
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        print(slug, len(h), (t.group(1).strip() if t else "?"))
    except Exception as e:
        print(slug, "ERR", e)
