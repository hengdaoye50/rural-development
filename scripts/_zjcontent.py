import json,sys,urllib.parse,urllib.request
base="https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"
def q(kw, site="330000000000", pg=20, p=1):
    p={"q":kw,"websiteid":site,"serviceId":"YcTOd1ftgC5dxzJ8RhCBN","cateid":"6N89tbnrVTYIQK5jt7q3T","p":p,"pg":pg}
    url=base+"?"+urllib.parse.urlencode(p)
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://search.zj.gov.cn/"})
    return json.load(urllib.request.urlopen(req,timeout=40))
d=q(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "330000000000")
items=d["data"]["appSearchResultBeanList"][0]["mapSearchResult"]["items"]
for it in items[:6]:
    dd=it["data"]
    print("=====",dd.get("title"),"|",dd.get("webname"),"|",dd.get("url"))
    print("CONTENT:", str(dd.get("vc_content"))[:700])
