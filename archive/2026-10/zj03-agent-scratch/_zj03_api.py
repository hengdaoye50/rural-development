# -*- coding: utf-8 -*-
"""查询浙江省政府网站群统一搜索 JSON 接口。
用法: python _zj03_api.py <websiteid> <query> [pg] [p]
"""
import sys, json, urllib.parse, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

SERVICE = "YcTOd1ftgC5dxzJ8RhCBN"
CATE = "6N89tbnrVTYIQK5jt7q3T"
BASE = "https://search.zj.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/app/info"


def search(websiteid, q, pg=10, p=1):
    url = (f"{BASE}?q={urllib.parse.quote(q)}&websiteid={websiteid}"
           f"&serviceId={SERVICE}&cateid={CATE}&p={p}&pg={pg}")
    raw = t.fetch(url)
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw[:800]}


if __name__ == "__main__":
    wid = sys.argv[1]
    q = sys.argv[2]
    pg = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    p = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    d = search(wid, q, pg, p)
    if "_raw" in d:
        print("RAW:", d["_raw"]); sys.exit(0)
    print("keys:", list(d.keys()))
    print(json.dumps(d, ensure_ascii=False)[:1200])
