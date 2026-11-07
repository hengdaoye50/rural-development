import sys, json, re, os, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("t", D + r"\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

POL = ["名单", "公布", "批复", "方案", "办法", "意见", "规划", "通知", "决定", "导则",
       "公告", "公示", "细则", "标准", "指南", "政策", "遴选", "评审", "部署", "总结"]
GOOD = ["片区", "重点村", "组团", "发展轴"]

for cc in sys.argv[1:]:
    p = D + rf"\_zj03_raw\harvest-{cc}.json"
    if not os.path.exists(p):
        continue
    items = json.load(open(p, encoding="utf-8"))
    seen = set()
    print(f"\n===== {cc} =====")
    for it in items:
        ti = it["title"]
        if ti in seen:
            continue
        if not any(k in ti for k in GOOD):
            continue
        if not any(k in ti for k in POL):
            continue
        body = t.strip(it["vc_content"])
        n = len(re.findall(r"[\u4e00-\u9fff]", body))
        seen.add(ti)
        dt = ""
        if it.get("createdate"):
            try:
                dt = datetime.datetime.fromtimestamp(int(it["createdate"]) / 1000,
                                                    datetime.timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
        print(f"  {dt} {n:5d}字 [{it['module'][:12]:12s}] {ti[:64]}")
        print(f"      {it['url']}")
