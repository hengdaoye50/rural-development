import json, re, sys, urllib.parse
from _tmp_probe import get

CACHE = {}


def unit_params(colurl):
    if colurl in CACHE:
        return CACHE[colurl]
    t = get(colurl)
    m = re.search(r'<script id="[^"]+"\s+src="[^"]*unitbuild\.js[^"]*"[^>]*>', t)
    if not m:
        return None
    qd = re.search(r'queryData="(\{.*?\})"', m.group(0))
    if not qd:
        return None
    d = json.loads(qd.group(1).replace("'", '"'))
    webid = re.search(r'webId="(\d+)"', m.group(0)).group(1)
    out = (webid, d["tplSetId"], d["pageId"], d["tagId"])
    CACHE[colurl] = out
    return out


def fetch(host, webid, tpl, pageid, tagid, page, size=10):
    q = {
        "parseType": "bulidstatic",
        "webId": webid,
        "tplSetId": tpl,
        "pageType": "column",
        "tagId": tagid,
        "editType": "null",
        "pageId": pageid,
        "paramJson": json.dumps({"pageNo": page, "pageSize": size}, separators=(",", ":")),
    }
    u = f"http://{host}/api-gateway/jpaas-publish-server/front/page/build/unit?" + urllib.parse.urlencode(q)
    t = get(u)
    try:
        html = json.loads(t)["data"]["html"]
    except Exception:
        html = t
    items = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        txt = re.sub(r"\s+", " ", txt)
        if txt:
            items.append((txt, m.group(1)))
    return items, html


if __name__ == "__main__":
    colurl = sys.argv[1]
    kw = re.compile(sys.argv[2] if len(sys.argv) > 2 else "片区")
    maxpage = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    showall = "--all" in sys.argv
    host = urllib.parse.urlparse(colurl).netloc
    p = unit_params(colurl)
    if not p:
        print("NO UNIT PARAMS")
        sys.exit(1)
    webid, tpl, pageid, tagid = p
    seen = set()
    for page in range(1, maxpage + 1):
        items, html = fetch(host, webid, tpl, pageid, tagid, page)
        new = [i for i in items if i[1] not in seen]
        if not new:
            break
        for txt, href in new:
            seen.add(href)
            if showall or kw.search(txt):
                print("**" if kw.search(txt) else "  ", page, txt[:95], "||", href)
    print("TOTAL", len(seen))
