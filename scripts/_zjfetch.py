import html
import re
import sys
import urllib.request


def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    raw = urllib.request.urlopen(req, timeout=45).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", "ignore")


def text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\u3000]+", " ", h)
    return re.sub(r"\n{3,}", "\n\n", h).strip()


if __name__ == "__main__":
    for u in sys.argv[1:]:
        print("=" * 30, u)
        try:
            t = text(get(u))
            print("LEN", len(t))
            print(t[:2500])
        except Exception as e:
            print("ERR", e)
