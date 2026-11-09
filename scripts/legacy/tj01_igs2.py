"""One-off TJ01 helper: loop per-district title query on the Tianjin policy index.

Usage: python tj01_igs2.py <kw> <FWJG1;FWJG2;...> [pages]
"""
import json
import sys
import urllib.parse
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
ROOT = "https://www.tjdl.gov.cn"


def run(kw, fwjg, pages):
    print(f"===== {fwjg} :: {kw} =====")
    for p in range(1, pages + 1):
        params = [
            ("index", "qszcwjk_index"),
            ("type", "POLICY"),
            ("pageSize", "20"),
            ("orderProperty", "PUBDATE"),
            ("orderDirection", "desc"),
            ("pageNumber", str(p)),
            ("filter[DOCTITLE-likeNotAnalyze]", kw),
            ("filter[FWJG]", fwjg),
        ]
        url = ROOT + "/igs/front/search/list.html?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as exc:  # noqa: BLE001
            print(f"  ## ERR {exc}")
            return
        rows = (d.get("page") or {}).get("content") or []
        if not rows:
            return
        for h in rows:
            print(f"  {(h.get('PUBDATE') or '')[:10]} | {h.get('FWZH') or ''} | {h.get('DOCTITLE')} | {h.get('DOCPUBURL')}")


if __name__ == "__main__":
    kw = sys.argv[1]
    fwjgs = sys.argv[2].split(";")
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for f in fwjgs:
        run(kw, f, pages)
