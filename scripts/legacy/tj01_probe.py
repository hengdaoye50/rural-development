"""One-off probe helper for TJ01 shard: fetch a page and list candidate links.

Not part of the pipeline. Usage:
  python tj01_probe.py links <url> [kw1 kw2 ...]
"""
import re
import sys
import urllib.request
from urllib.parse import urljoin

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def links(html, base, kws):
    out = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, text = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        if any(k in text for k in kws):
            out.append((text, urljoin(base, href)))
    seen, uniq = set(), []
    for t, u in out:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((t, u))
    return uniq


if __name__ == "__main__":
    mode, url = sys.argv[1], sys.argv[2]
    kws = sys.argv[3:]
    html = fetch(url)
    if mode == "links":
        for t, u in links(html, url, kws):
            print(f"{t}\t{u}")
    elif mode == "text":
        body = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
        body = re.sub(r"(?s)<[^>]+>", "\n", body)
        body = re.sub(r"\n{2,}", "\n", body)
        print(body)
