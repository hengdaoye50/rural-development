"""Temporary helper: fetch a .gov.cn page and extract the article body as Markdown."""
import hashlib
import os
import re
import subprocess
import sys
import tempfile

from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

DROP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "iframe", "form"]


def fetch(url):
    """Use curl.exe: some .gov.cn sites answer 502 to python-requests TLS fingerprints."""
    fd, tmp = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        subprocess.run(["curl.exe", "-s", "-L", "--max-time", "50",
                        "-H", "User-Agent: " + UA,
                        "-H", "Accept-Language: zh-CN,zh;q=0.9",
                        "-o", tmp, url], check=False)
        with open(tmp, "rb") as f:
            raw = f.read()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if not raw:
        raise RuntimeError("empty response " + url)
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:3000], re.I)
    enc = "utf-8"
    if m:
        enc = m.group(1).decode("ascii", "ignore").lower()
        if enc in ("gb2312", "gbk", "gb18030"):
            enc = "gb18030"
    try:
        return raw.decode(enc, "ignore")
    except LookupError:
        return raw.decode("utf-8", "ignore")


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
    if best is not None:
        return best
    return soup.body or soup


def to_md(node):
    out = []
    for el in node.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        txt = el.get_text("", strip=True)
        if not txt:
            continue
        if el.name.startswith("h"):
            out.append("#" * int(el.name[1]) + " " + txt)
        elif el.name == "li":
            out.append("- " + txt)
        else:
            out.append(txt)
    return out


def main():
    url = sys.argv[1]
    out = sys.argv[2]
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(DROP_TAGS):
        t.decompose()
    root = pick_root(soup)
    text = "\n\n".join(to_md(root))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    body = BeautifulSoup(html, "html.parser")
    for t in body(DROP_TAGS):
        t.decompose()
    title = body.title.get_text(strip=True) if body.title else ""
    print("URL:", url)
    print("TITLE:", title)
    print("CHARS:", len(text))
    print("SHA256:", hashlib.sha256(text.encode("utf-8")).hexdigest())
    print("---HEAD---")
    print(text[:900])
    print("---TERMS---")
    for kw in ["示范带", "片区", "画廊", "走廊", "万元", "亿元"]:
        for h in [m.start() for m in re.finditer(kw, text)][:3]:
            print("[" + kw + "]", text[max(0, h - 60):h + 80].replace("\n", " "))


if __name__ == "__main__":
    main()
