# -*- coding: utf-8 -*-
"""荆门市政府网站群全文检索 API 客户端（覆盖京山市 webid=34、钟祥市 webid=33）。"""
import json, sys, urllib.request

API = "https://www.jingmen.gov.cn/api/xunsearch/json"
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
      "Content-Type": "application/json", "Accept": "application/json",
      "Accept-Encoding": "identity", "Connection": "close"}


def search(q, webid=0, page=1, **kw):
    body = {"query": q, "page": page, "cataid": 0, "webid": webid, "model": "",
            "type": "", "sort": "related", "range": "all", "rangeDate": "全部"}
    body.update(kw)
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers=HD, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=40).read().decode("utf-8"))


if __name__ == "__main__":
    q = sys.argv[1]
    webids = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0]
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for w in webids:
        for p in range(1, pages + 1):
            d = search(q, webid=w, page=p)
            data = d.get("data")
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("list") or data.get("records") or []
            else:
                items = []
            if not items:
                print("webid=%s page=%s raw=%s" % (w, p, json.dumps(d, ensure_ascii=False)[:400]))
                break
            for it in items:
                print("%s | %s | %s | %s" % (w, it.get("publishTime") or it.get("date") or "",
                                            (it.get("title") or "").replace("<em>", "").replace("</em>", ""),
                                            it.get("blink") or it.get("url") or it.get("id")))
