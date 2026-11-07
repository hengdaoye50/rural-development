import sys, json, re, os, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("t", D + r"\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

URBAN = ["详细规划", "控制性详细规划", "控规", "地块", "单元", "出让", "征收", "规划修改",
         "批前公示", "批后公告", "选址", "修建性", "城市设计", "不动产", "用地", "工程规划许可"]
SIGNAL = ["片区组团", "组团片区", "重点村", "发展轴", "片区化", "强村公司", "两进两回",
          "和美乡村", "乡村振兴", "未来乡村", "乡村运营", "共同富裕示范带", "强城兴村",
          "组团发展", "新时代千万工程"]

def score(title, body):
    s = 0
    if any(k in title for k in ["片区组团", "组团片区", "重点村", "发展轴", "片区化"]):
        s += 6
    n_pq = body.count("片区")
    s += min(n_pq, 8)
    if "片区组团" in body or "组团片区" in body:
        s += 5
    if any(k in title for k in URBAN):
        s -= 12
    if not any(k in title + body for k in SIGNAL):
        s -= 8
    return s

def run(cc):
    p = D + rf"\_zj03_raw\harvest-{cc}.json"
    if not os.path.exists(p):
        return []
    items = json.load(open(p, encoding="utf-8"))
    out = []
    for it in items:
        body = t.strip(it["vc_content"])
        n = len(re.findall(r"[\u4e00-\u9fff]", body))
        sc = score(it["title"], body)
        if sc < 8:
            continue
        dt = ""
        if it.get("createdate"):
            try:
                dt = datetime.datetime.fromtimestamp(int(it["createdate"]) / 1000,
                                                    datetime.timezone.utc).strftime("%Y-%m-%d")
            except Exception:
                pass
        out.append({"cc": cc, "sc": sc, "dt": dt, "n": n, "module": it["module"],
                    "webname": it["webname"], "title": it["title"], "url": it["url"],
                    "regionname": it["regionname"]})
    out.sort(key=lambda r: (-r["sc"], r["dt"]), reverse=False)
    out.sort(key=lambda r: (r["dt"], r["sc"]), reverse=True)
    return out

if __name__ == "__main__":
    ccs = sys.argv[1:] or ["330203", "330206", "330212", "330324", "330326", "330327",
                           "330328", "330329", "330300", "330200", "330000"]
    allr = []
    for cc in ccs:
        r = run(cc)
        print(f"=== {cc} kept={len(r)}")
        for x in r[:int(os.environ.get("TOPN", "25"))]:
            print(f"  {x['sc']:3d} {x['dt']} [{x['module'][:10]:10s}] {x['title'][:66]}")
            print(f"      {x['url']}")
        allr += r
    json.dump(allr, open(D + r"\_zj03_raw\triage.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("TOTAL", len(allr))
