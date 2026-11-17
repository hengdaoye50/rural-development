import urllib.request,re
from pypdf import PdfReader
u="http://www.sx.gov.cn/cms_files/filemanager/1539267/attach/20269/95fb3c56f9d64e94aa678f05a0d3947c.pdf"
raw=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=90).read()
open("data/stage/_tmp.pdf","wb").write(raw)
r=PdfReader("data/stage/_tmp.pdf")
txt="\n".join((p.extract_text() or "") for p in r.pages)
open("reports/qa/_sx_plan.txt","w",encoding="utf-8").write(txt)
names=["越乡名仕文化","稽山鉴水","红色文化传承","渔乐童趣历史","茶园酒香乐善","生态宜居和美","放翁牧歌","鉴湖水韵","古越宋韵","稽山舜源","品味千年","醉美岁月","慢享生活","溯源走心","田上枫景","小吃经","书圣风"]
for n in names:
    idx=[m.start() for m in re.finditer(n,txt)]
    print(n, len(idx))
    for i in idx[:2]:
        print("   ...",txt[max(0,i-120):i+160].replace("\n",""))
