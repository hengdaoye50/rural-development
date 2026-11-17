import json,sys,urllib.parse,urllib.request
def q(kw, site="330000000000", pg=20):
    base="https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"
    p={"q":kw,"websiteid":site,"serviceId":"YcTOd1ftgC5dxzJ8RhCBN","cateid":"6N89tbnrVTYIQK5jt7q3T","p":1,"pg":pg}
    url=base+"?"+urllib.parse.urlencode(p)
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://search.zj.gov.cn/"})
    return json.load(urllib.request.urlopen(req,timeout=40))
if __name__=="__main__":
    kw=sys.argv[1]; site=sys.argv[2] if len(sys.argv)>2 else "330000000000"
    d=q(kw,site)
    try:
        items=d["data"]["appSearchResultBeanList"][0]["mapSearchResult"]["items"]
    except Exception as e:
        print("ERR",e, json.dumps(d,ensure_ascii=False)[:1500]); sys.exit()
    print("hits",len(items))
    for it in items[:20]:
        dd=it.get("data",{})
        title=[v for k,v in dd.items() if k.startswith("bu11etin") or k.startswith("bulletin")]
        t=None
        for k,v in dd.items():
            if "title" in k.lower() or "name" in k.lower(): t=v
        print("---")
        print({k:v for k,v in dd.items() if len(str(v))<160})
