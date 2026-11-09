import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_probe import fetch  # noqa: E402


def items(html, base_dir):
    out = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href = m.group(1)
        text = re.sub(r"<[^>]+>", "", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if not text or len(text) < 8:
            continue
        if href.startswith("#") or href.lower().startswith("javascript"):
            continue
        if not re.search(r"/t\d{8}_\d+\.html?$|/\d{6}/", href, re.I):
            continue
        out.append((text, base_dir + href if not href.startswith("http") else href))
    seen, uniq = set(), []
    for t, u in out:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((t, u))
    return uniq


def main():
    pattern = sys.argv[1]  # e.g. https://x.gov.cn/ZWGK0/TZGG/index{}.html
    pages = int(sys.argv[2])
    kw = sys.argv[3].split(",")
    base_dir = re.match(r"(https?://[^/]+)", pattern).group(1)
    for p in range(pages):
        url = pattern.format("" if p == 0 else f"_{p}")
        try:
            html = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"## page {p} ERR {exc}")
            break
        rows = items(html, base_dir)
        if not rows:
            print(f"## page {p} empty")
            break
        for t, u in rows:
            if any(k in t for k in kw):
                print(f"{t}\t{u}")


if __name__ == "__main__":
    main()
