"""Temporary helper: fetch several URLs, extract body text, report key-term hits."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _tmp_fetch import fetch, to_md, DROP_TAGS  # noqa: E402

from bs4 import BeautifulSoup  # noqa: E402
import re  # noqa: E402

OUT = Path(os.environ.get("TEMP", ".")) / "gd02"
OUT.mkdir(parents=True, exist_ok=True)


def pick_root(soup):
    for sel in ["#zoom", ".TRS_Editor", "#content", ".content", "#zoomcon",
                ".article-content", ".view", "#article", ".news_content",
                ".Article", "#print", ".main-content", ".detail", "#mainText"]:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 300:
            return node
    best, best_len = None, 0
    for d in soup.find_all("div"):
        ps = d.find_all("p", recursive=False)
        if len(ps) < 3:
            continue
        total = sum(len(p.get_text(strip=True)) for p in ps)
        if total > best_len:
            best, best_len = d, total
    return best if best is not None else (soup.body or soup)


def run(slug, url):
    try:
        html = fetch(url)
    except Exception as exc:  # noqa: BLE001
        print("[FAIL] %s %s %s" % (slug, url, exc))
        return
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(DROP_TAGS):
        t.decompose()
    text = re.sub(r"\n{3,}", "\n\n", "\n\n".join(to_md(pick_root(soup)))).strip()
    title = BeautifulSoup(html, "html.parser").title
    title = title.get_text(strip=True) if title else ""
    p = OUT / (slug + ".md")
    p.write_text(text, encoding="utf-8", newline="\n")
    print("\n=== %s | %s" % (slug, title))
    print("    chars=%d  -> %s" % (len(text), p))
    print("    url=%s" % url)
    for kw in ["示范带", "片区", "画廊", "走廊"]:
        hits = [m.start() for m in re.finditer(kw, text)]
        if hits:
            print("    [%s x%d] %s" % (kw, len(hits), text[max(0, hits[0] - 50):hits[0] + 70].replace("\n", " ")))


if __name__ == "__main__":
    jobs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    for slug, url in jobs:
        run(slug, url)
