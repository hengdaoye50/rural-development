import json, re, sys
from _tmp_probe import get

# usage: python _tmp_cmslist.py host webId tplSetId pageId tagId [page]
host = sys.argv[1]
webid = sys.argv[2]
tpl = sys.argv[3]
pageid = sys.argv[4]
tagid = sys.argv[5]
page = sys.argv[6] if len(sys.argv) > 6 else "1"

import urllib.parse

u = (
    f"http://{host}/api-gateway/jpaas-publish-server/front/page/build/unit"
    f"?parseType=bulidstatic&webId={webid}&tplSetId={tpl}&pageType=column"
    f"&tagId={urllib.parse.quote(tagid)}&editType=null&pageId={pageid}&currentPage={page}"
)
t = get(u)
try:
    d = json.loads(t)
    html = d["data"]["html"]
except Exception:
    html = t
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*(?:<[^>]+>)*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})?', html, re.S):
    txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    txt = re.sub(r"\s+", " ", txt)
    print((m.group(3) or ""), "|", txt[:100], "||", m.group(1))
mm = re.search(r"共\s*(\d+)\s*页", html)
print("PAGES", mm.group(1) if mm else "?")
if "--raw" in sys.argv:
    print(html)
