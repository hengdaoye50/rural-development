import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"


def query(kw, site, pages=2, pg=20):
    out = []
    for p in range(1, pages + 1):
        par = {
            "q": kw,
            "websiteid": site,
            "serviceId": "YcTOd1ftgC5dxzJ8RhCBN",
            "cateid": "6N89tbnrVTYIQK5jt7q3T",
            "p": p,
            "pg": pg,
        }
        req = urllib.request.Request(
            BASE + "?" + urllib.parse.urlencode(par),
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://search.zj.gov.cn/"},
        )
        d = None
        for _ in range(3):
            try:
                d = json.load(urllib.request.urlopen(req, timeout=45))
                break
            except Exception:
                time.sleep(3)
        if not d:
            break
        try:
            items = d["data"]["appSearchResultBeanList"][0]["mapSearchResult"]["items"]
        except Exception:
            break
        out += [it["data"] for it in items]
        time.sleep(0.5)
    return out


def strip(s):
    s = re.sub(r"<script.*?</script>", "", s or "", flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s)


if __name__ == "__main__":
    kw = sys.argv[1]
    site = sys.argv[2] if len(sys.argv) > 2 else "330000000000"
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    items = query(kw, site, pages)
    print("### q=", kw, "site=", site, "n=", len(items))
    for dd in items:
        u = dd.get("url") or ""
        if not u.startswith("http"):
            continue
        t = strip(dd.get("title"))
        b = strip(dd.get("vc_content"))
        if "片区" in t or "片区" in b:
            print("-", dd.get("webname"), "|", t[:70], "|", u[:110], "|len", len(b))
