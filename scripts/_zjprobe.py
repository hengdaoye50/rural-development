import json,sys,urllib.parse,urllib.request
base="https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"
def q(kw, site="330000000000", pg=20, p=1):
    p={"q":kw,"websiteid":site,"serviceId":"YcTOd1ftgC5dxzJ8RhCBN","cateid":"6N89tbnrVTYIQK5jt7q3T","p":p,"pg":pg}
    url=base+"?"+urllib.parse.urlencode(p)
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://search.zj.gov.cn/"})
    return json.load(urllib.request.urlopen(req,timeout=40))
d=q(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "330000000000")
bl=d["data"]["appSearchResultBeanList"][0]
print("total?",bl.get("total"), list(bl.keys()))
items=bl["mapSearchResult"]["items"]
print("n",len(items))
print(json.dumps(list(items[0]["data"].keys()),ensure_ascii=False))
