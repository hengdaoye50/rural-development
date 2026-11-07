# -*- coding: utf-8 -*-
"""探测湖北县级政府站站内检索入口。"""
import re, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Encoding": "identity", "Connection": "close"}

sites = {
    "echeng": "https://www.echeng.gov.cn/",
    "zhongxiang": "https://www.zhongxiang.gov.cn/",
    "jingshan": "https://www.jingshan.gov.cn/",
    "xiaochang": "https://www.xiaochang.gov.cn/",
    "jingzhouqu": "https://www.jingzhouqu.gov.cn/",
    "songzi": "https://www.hbsz.gov.cn/",
    "tuanfeng": "https://www.tfzf.gov.cn/",
    "yingshan": "http://www.yingshan.gov.cn/",
}

for k, u in sites.items():
    try:
        raw = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=25).read()
        html = raw.decode("utf-8", errors="replace")
        forms = re.findall(r'(?is)<form[^>]*>.*?</form>', html)[:3]
        hits = re.findall(r'(?i)(?:action|href)="([^"]*(?:search|sousuo|so\.|ss\.)[^"]*)"', html)
        print(k, "|title:", (re.search(r'(?is)<title>(.*?)</title>', html) or [None, "?"])[1].strip()[:40])
        print("   search-links:", list(dict.fromkeys(hits))[:6])
        for f in forms:
            print("   form:", re.sub(r"\s+", " ", f)[:200])
    except Exception as e:
        print(k, "FAIL", e)
