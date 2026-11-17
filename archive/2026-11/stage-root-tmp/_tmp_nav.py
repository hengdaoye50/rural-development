import re
import _tmp_fetch as f

SITES = {
    "岳阳县": "http://www.yyx.gov.cn/",
    "汉寿县": "http://www.hanshou.gov.cn/",
    "澧县": "http://www.lixian.gov.cn/",
    "赫山区": "http://www.heshan.gov.cn/",
    "汨罗市": "http://www.miluo.gov.cn/",
    "武陵区": "http://www.wuling.gov.cn/",
    "临澧县": "http://www.linli.gov.cn/",
}

for name, base in SITES.items():
    print("=== ", name, base)
    try:
        h = f.fetch(base, timeout=20)
    except Exception as e:
        print("  ERR", type(e).__name__, str(e)[:70])
        continue
    seen = set()
    for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        href = m.group(1)
        lab = re.sub(r'(?s)<[^>]+>', '', m.group(2)).strip()
        if not any(k in lab for k in ("报告", "公开", "信息公开")):
            continue
        key = (lab, href)
        if key in seen:
            continue
        seen.add(key)
        print("   ", lab[:40], "|", href)
        if len(seen) > 14:
            break
