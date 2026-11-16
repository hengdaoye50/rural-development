import sys
import _tmp_fetch as f

CAND = [
    "http://www.hnheshan.gov.cn/",
    "http://www.lix.gov.cn/",
    "http://www.lixian.gov.cn/",
    "http://www.jinshi.gov.cn/",
    "http://www.hengshan.gov.cn/",
]

for url in CAND:
    try:
        h = f.fetch(url, timeout=15)
        t = f.text_of(h)
        title = ""
        import re
        m = re.search(r'(?is)<title>(.*?)</title>', h)
        if m:
            title = re.sub(r'\s+', ' ', m.group(1)).strip()[:50]
        print("OK  ", url, "len", len(h), "title:", title)
    except Exception as e:
        print("FAIL", url, type(e).__name__, str(e)[:60])
