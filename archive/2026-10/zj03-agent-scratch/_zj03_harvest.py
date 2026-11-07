# -*- coding: utf-8 -*-
"""按县抓取浙江省政府网站群搜索 API，收集涉及片区的候选文件。
用法: python _zj03_harvest.py <county_code> [maxpage]
输出: _zj03_raw/harvest-<county>.json (list of items)
"""
import sys, json, os, time, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("a", D + r"\_zj03_api.py")
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

KWS = ["片区组团", "重点村", "片区", "组团片区", "发展轴", "和美乡村", "乡村振兴",
       "强村公司", "两进两回", "共同富裕示范带", "片区化", "乡村振兴示范", "未来乡村",
       "乡村运营", "组团发展", "强城兴村"]

def main():
    cc = sys.argv[1]
    maxpage = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    wid = cc + "000000"
    seen, items = set(), []
    for kw in KWS:
        for p in range(1, maxpage + 1):
            try:
                d = a.search(wid, kw, 20, p)
            except Exception as e:
                print("  ERR", kw, p, e); continue
            bl = (d.get("data") or {}).get("appSearchResultBeanList") or []
            got = 0
            for b in bl:
                msr = b.get("mapSearchResult") or {}
                for it in (msr.get("items") or []):
                    dd = it.get("data") or {}
                    u = dd.get("url") or ""
                    if not u or u in seen:
                        continue
                    seen.add(u); got += 1
                    items.append({
                        "kw": kw, "url": u,
                        "title": dd.get("title_h") or dd.get("title_str") or "",
                        "webname": dd.get("webname") or "",
                        "module": dd.get("module") or "",
                        "regionname": dd.get("regionname") or "",
                        "createdate": dd.get("createdate"),
                        "vc_content": dd.get("vc_content") or "",
                        "vc_attach": dd.get("vc_attach") or "",
                        "websiteName": dd.get("websiteName") or "",
                    })
            if got == 0:
                break
            time.sleep(0.3)
        print(f"  {kw}: cumulative={len(items)}")
    os.makedirs(D + r"\_zj03_raw", exist_ok=True)
    out = D + rf"\_zj03_raw\harvest-{cc}.json"
    json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"WROTE {out} n={len(items)}")

if __name__ == "__main__":
    main()
