import re
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
urls = [
    "https://www.changde.gov.cn/zwgk/public/6616759/2858077571.html",
    "https://www.taoyuan.gov.cn/zwgk/public/6616339/1133252511.html",
    "https://www.hxw.gov.cn/content/2025/03/12/14711867.html",
    "https://cdlyh.changde.gov.cn/zwgk/public/6617378/2083308551.html",
]
for u in urls:
    raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=25).read()
    s = raw.decode("utf-8", "ignore")
    print("=" * 20, u, len(s))
    for m in re.findall(r'<(?:div|td|section|article)[^>]*(?:class|id)="([^"]+)"', s)[:30]:
        print("  attr:", m)
    for pat in (r"<h1[^>]*>(.*?)</h1>", r"来源[：:][^<]{0,40}", r"20\d\d-\d\d-\d\d(?:\s+\d\d:\d\d)?"):
        hits = re.findall(pat, s, re.S)
        print(" ", pat, "->", hits[:6])

try:
    import bs4

    print("bs4", bs4.__version__)
except Exception as e:  # noqa: BLE001
    print("no bs4", e)
