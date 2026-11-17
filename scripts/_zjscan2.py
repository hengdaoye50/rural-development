import csv,json,re,sys,time,urllib.parse,urllib.request,html
base="https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"
def gq(kw, site, pg=20, p=1):
    par={"q":kw,"websiteid":site,"serviceId":"YcTOd1ftgC5dxzJ8RhCBN","cateid":"6N89tbnrVTYIQK5jt7q3T","p":p,"pg":pg}
    req=urllib.request.Request(base+"?"+urllib.parse.urlencode(par),headers={"User-Agent":"Mozilla/5.0","Referer":"https://search.zj.gov.cn/"})
    for i in range(3):
        try: return json.load(urllib.request.urlopen(req,timeout=45))
        except Exception: time.sleep(3)
    return {}
def strip(s):
    s=re.sub(r"<script.*?</script>","",s or "",flags=re.S); s=re.sub(r"<[^>]+>","",s)
    return html.unescape(s)
def search(kw, site, pages=1):
    out=[]
    for p in range(1,pages+1):
        d=gq(kw,site,p=p)
        try: items=d["data"]["appSearchResultBeanList"][0]["mapSearchResult"]["items"]
        except Exception: break
        out+= [it["data"] for it in items]; time.sleep(0.5)
    return out
targets=["A330297 330111 壶源流域场口片区","A330298 330111 壶源流域湖源片区","A330323 330182 安仁共富联合体片区","A330324 330182 三江诗路片区","A330325 330182 莓好农园片区","A330327 330182 西乡农创片区","A330335 330503 全球农遗荻港共富片区","A330359 330521 庙桥枕水片区","A330361 330521 二都绿洲片区","A330367 330681 田上枫景片区","A330371 331002 大陈片区","A330372 331003 柔川片区","A330373 331022 亭旁片区","A330374 331081 大栈头片区","A330402 330110 花漾仁和片区","A330403 330127 千岛湖秀水千岛片区","A330404 330182 稻香茶韵片区","A330418 331181 大溪头片区","A330419 330825 黄茶漫旅片区","A330424 330603 古越宋韵片区","A330431 330683 小吃经共富组团","A330432 330683 书圣风片区","A330434 330602 越乡名仕文化片区","A330437 330602 渔乐童趣历史片区","A330438 330602 茶园酒香乐善片区","A330440 330602 放翁牧歌片区","A330441 330602 鉴湖水韵片区"]
for t in targets:
    aid,cc,name=t.split(" ")
    core=re.sub(r"(共富)?片区$|片区$","",name)
    site=cc+"000000"
    hits=search(core,site)
    keep=[]
    for dd in hits:
        u=dd.get("url") or ""
        if not u.startswith("http"): continue
        body=strip(dd.get("vc_content")); title=strip(dd.get("title"))
        if name in body or name in title:
            keep.append(("EXACT",dd.get("webname"),title,u,len(body)))
        elif core+"片区" in body:
            keep.append(("CORE+片区",dd.get("webname"),title,u,len(body)))
        elif core in body or core in title:
            keep.append(("CORE",dd.get("webname"),title,u,len(body)))
    print("###",aid,cc,name,"core=",core,"countyhits",len(hits),"keep",len(keep))
    for k in keep[:8]:
        print("   ",k[0],"|",k[1],"|",k[2][:55],"|",k[3][:95],"|len",k[4])
    sys.stdout.flush()
