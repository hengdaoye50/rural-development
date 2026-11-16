import re, sys
import _tmp_fetch as f

base = "https://www.changde.gov.cn/zwgk/public/column/6616759?type=4&catId=6719140&action=list&nav=3"
for extra in ["&page=2", "&pageIndex=2", "&pageNo=2", "&currentPage=2"]:
    url = base + extra
    try:
        h = f.fetch(url, timeout=20)
    except Exception as e:
        print("ERR", extra, type(e).__name__, str(e)[:50])
        continue
    labs = []
    for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        lab = re.sub(r'\s+', ' ', re.sub(r'(?s)<[^>]+>', '', m.group(2))).strip()
        if '政府工作报告' in lab and ('县' in lab or '市' in lab or '区' in lab):
            labs.append(lab[:40] + " | " + m.group(1)[:60])
    print("==", extra, "len", len(h), "hits", len(labs))
    for x in labs[:12]:
        print("   ", x)
