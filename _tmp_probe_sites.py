import re, sys
from _tmp_fetch import fetch, decode

sites = [
    'http://www.zhenjiang.gov.cn/',
    'http://www.yangzhong.gov.cn/',
    'http://www.jurong.gov.cn/',
    'http://www.dantu.gov.cn/',
    'http://www.yizheng.gov.cn/',
    'http://www.taixing.gov.cn/',
    'http://www.yangzhou.gov.cn/',
    'http://www.taizhou.gov.cn/',
    'http://nynct.jiangsu.gov.cn/',
    'http://www.jianyang.gov.cn/',
    'http://www.shifang.gov.cn/',
    'http://www.zg.gov.cn/',
]
for s in sites:
    try:
        st, raw = fetch(s, timeout=25)
        t = decode(raw)
        # find search form action + hidden inputs
        forms = re.findall(r"<form[^>]*action=['\"]?([^'\" >]+)[^>]*>", t, re.I)
        hid = re.findall(r"<input[^>]*type=['\"]hidden['\"][^>]*>", t, re.I)
        print('OK  %-40s %s  len=%d' % (s, st, len(t)))
        print('    forms:', forms[:4])
        for h in hid[:12]:
            if 'websiteid' in h.lower() or 'searchid' in h.lower() or 'siteid' in h.lower() or 'columnid' in h.lower():
                print('    hid:', h.strip()[:160])
    except Exception as e:
        print('ERR %-40s %s %s' % (s, type(e).__name__, e))
