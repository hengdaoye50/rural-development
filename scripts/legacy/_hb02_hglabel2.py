# -*- coding: utf-8 -*-
"""黄冈平台 label API：取栏目文章列表（带 Referer 与时间戳）。"""
import re, sys, time, urllib.request

HD = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept-Encoding": "identity", "Connection": "close",
      "Accept": "text/html,*/*", "Referer": "https://www.chinays.gov.cn/zwgk/public/column/6636628?type=4&catId=7027079&action=list"}
host = sys.argv[1]
site, organ, cat = sys.argv[2], sys.argv[3], sys.argv[4]
size = sys.argv[5] if len(sys.argv) > 5 else "30"
kws = sys.argv[6].split(",") if len(sys.argv) > 6 else None
u = ("https://%s/zwgk/site/label/8888?_=%f&labelName=publicInfoList&siteId=%s&organId=%s"
     "&pageSize=%s&catId=%s&type=4&length=300&dateFormat=yyyy-MM-dd&file=/c2/xxgk/publicInfoList_newest_zc01"
     % (host, time.time(), site, organ, cat, size))
h = urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=40).read().decode("utf-8", "replace")
print("len", len(h))
blocks = re.findall(r"(?is)<li[^>]*>.*?</li>", h)
print("li blocks", len(blocks))
cnt = 0
for b in blocks:
    m = re.search(r'href="([^"]+)"', b)
    t = re.sub(r"<[^>]+>", "", b)
    t = re.sub(r"\s+", " ", t).strip()
    if not m or len(t) < 6:
        continue
    if kws and not any(k in t for k in kws):
        continue
    cnt += 1
    print("  %s\n    -> %s" % (t[:90], m.group(1)))
print("matched", cnt)
