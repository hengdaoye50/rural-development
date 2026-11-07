# -*- coding: utf-8 -*-
"""批量抓取文章正文 → _zj03_raw/txt/<id>.json
用法: python _zj03_batch.py <urlsfile>
urlsfile: 每行 "<id>\t<url>"
"""
import sys, os, json, re, time, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
spec = importlib.util.spec_from_file_location("t", D + r"\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
spec2 = importlib.util.spec_from_file_location("art", D + r"\_zj03_art.py")
art = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(art)

os.makedirs(D + r"\_zj03_raw\txt", exist_ok=True)
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    _id, url = line.split("\t")
    out = D + rf"\_zj03_raw\txt\{_id}.json"
    if os.path.exists(out):
        d = json.load(open(out, encoding="utf-8"))
        print(f"{_id}: cached chars={d['chars']}")
        continue
    try:
        ht = t.fetch(url)
    except Exception as e:
        print(f"{_id}: FETCH-ERR {e} :: {url}")
        continue
    title = art.clean_title(ht)
    m = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', ht)
    if m:
        c = t.strip(m.group(1)).replace("\n", " ")
        if 4 < len(c) < 140 and "首页" not in c:
            title = c
    body = art.to_md(art.pick_body(ht))
    chars = len(re.findall(r"[\u4e00-\u9fff]", body))
    json.dump({"id": _id, "url": url, "title": title, "body_md": body, "chars": chars},
              open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{_id}: chars={chars} | {title[:60]}")
    time.sleep(0.4)
