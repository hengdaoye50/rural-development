import csv,json,re,sys,time,urllib.parse,urllib.request,html
base="https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"
def gq(kw, site="330000000000", pg=20, p=1):
    par={"q":kw,"websiteid":site,"serviceId":"YcTOd1ftgC5dxzJ8RhCBN","cateid":"6N89tbnrVTYIQK5jt7q3T","p":p,"pg":pg}
    req=urllib.request.Request(base+"?"+urllib.parse.urlencode(par),headers={"User-Agent":"Mozilla/5.0","Referer":"https://search.zj.gov.cn/"})
    for i in range(3):
        try: return json.load(urllib.request.urlopen(req,timeout=45))
        except Exception as e:
            time.sleep(3)
    return {}
def strip(s):
    s=re.sub(r"<script.*?</script>","",s or "",flags=re.S)
    s=re.sub(r"<[^>]+>","",s)
    return html.unescape(s)
def search(kw, site="330000000000", pages=1):
    out=[]
    for p in range(1,pages+1):
        d=gq(kw,site,p=p)
        try: items=d["data"]["appSearchResultBeanList"][0]["mapSearchResult"]["items"]
        except Exception: break
        for it in items: out.append(it["data"])
        time.sleep(0.6)
    return out
def scan(name,site="330000000000",pages=1):
    core=re.sub(r"(共富)?片区$","",name)
    seen={}
    for kw in (name, core):
        for dd in search(kw,site,pages):
            u=dd.get("url") or ""
            if u.startswith("linkurl"): continue
            if not u.startswith("http"): continue
            body=strip(dd.get("vc_content"))
            title=strip(dd.get("title"))
            key=u
            hit=[]
            for cand in (name, core+"片区", core):
                if len(cand)>=3 and (cand in body or cand in title): hit.append(cand)
            if hit:
                seen.setdefault(key,{"url":u,"title":title,"web":dd.get("webname"),"content":body,"hits":hit})
        time.sleep(0.6)
    return list(seen.values())
if __name__=="__main__":
    rows=list(csv.DictReader(open("data/stage/candidates/pending-areas-ZJ.csv",encoding="utf-8-sig")))
    rows.sort(key=lambda r: r["area_id"])
    for r in rows[45:]:
        res=scan(r["name"])
        print("###",r["area_id"],r["county_code"],r["name"],"=>",len(res))
        for x in res[:6]:
            print("   ",x["web"],"|",x["title"][:60],"|",x["url"][:100],"|hits",x["hits"][:2],"|len",len(x["content"]))
        sys.stdout.flush()
