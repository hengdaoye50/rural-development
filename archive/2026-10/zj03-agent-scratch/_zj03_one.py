import sys, json, re, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
cc = sys.argv[1]
needle = sys.argv[2]
items = json.load(open(D + rf"\_zj03_raw\harvest-{cc}.json", encoding="utf-8"))
for it in items:
    if needle in it["title"]:
        print("TITLE:", it["title"])
        print("URL:", it["url"])
        print("MODULE:", it["module"], "| WEBSITE:", it["websiteName"])
        print("VC_CONTENT len:", len(it["vc_content"]))
        print("VC_CONTENT:", it["vc_content"][:600])
        print("VC_ATTACH:", str(it["vc_attach"])[:800])
        print("-" * 60)
