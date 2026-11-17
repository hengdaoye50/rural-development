import re
t=open("reports/qa/_sx_plan.txt",encoding="utf-8").read()
for kw in ["越城","诸暨","嵊州","柯桥"]:
    print("####",kw, t.count(kw))
    for m in list(re.finditer(kw,t))[:4]:
        print("  ...",t[max(0,m.start()-100):m.start()+220].replace("\n",""))
print("#### 片区 count",t.count("片区"))
