"""One-off TJ01 helper: query the Tianjin city-wide policy index (IGS).

Not part of the pipeline.
Usage:
  python tj01_igs.py [--index IDX] [--pages N] [--filter K=V ...] -- KW1 [KW2 ...]
Each KW is applied as filter[DOCTITLE-likeNotAnalyze] when --title, otherwise
filter[POLICYCONTENT-like] (full-text).
"""
import argparse
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


def query(index, page, extra, kw_field, kw):
    params = [
        ("index", index),
        ("type", "POLICY"),
        ("pageSize", "20"),
        ("orderProperty", "PUBDATE"),
        ("orderDirection", "desc"),
        ("pageNumber", str(page)),
        (f"filter[{kw_field}]", kw),
    ]
    params.extend(extra)
    url = ROOT + "/igs/front/search/list.html?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="qszcwjk_index")
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--field", default="DOCTITLE-likeNotAnalyze")
    ap.add_argument("--filter", action="append", default=[])
    ap.add_argument("kws", nargs="+")
    a = ap.parse_args()
    extra = []
    for f in a.filter:
        k, _, v = f.partition("=")
        extra.append((f"filter[{k}]", v))
    for kw in a.kws:
        print(f"===== {kw} =====")
        seen = set()
        for p in range(1, a.pages + 1):
            try:
                d = query(a.index, p, extra, a.field, kw)
            except Exception as exc:  # noqa: BLE001
                print(f"## ERR {exc}")
                break
            page = d.get("page") or {}
            rows = page.get("content") or []
            print(f"## page {p} total={page.get('totalElements')} n={len(rows)}")
            if not rows:
                break
            for h in rows:
                u = h.get("DOCPUBURL") or ""
                if u in seen:
                    continue
                seen.add(u)
                print(
                    "{pub} | {qy} | {fw} | {zh} | {t} | {url}".format(
                        pub=(h.get("PUBDATE") or "")[:10],
                        qy=h.get("QYJB") or "",
                        fw=h.get("FWJG") or "",
                        zh=h.get("FWZH") or "",
                        t=h.get("DOCTITLE") or "",
                        url=u,
                    )
                )


if __name__ == "__main__":
    sys.exit(main())
