"""临时检索工具：抓取 URL，抽正文，按关键词定位（不参与管线）。"""
import html
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TAG = re.compile(r"<[^>]+>")
DROP = re.compile(r"(?is)<(script|style|noscript|iframe)[^>]*>.*?</\1>")
BLOCK = re.compile(r"(?i)</?(p|div|br|tr|li|h[1-6]|table|section|article)[^>]*>")


def to_text(raw: bytes) -> str:
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000], re.I)
    enc = m.group(1).decode("ascii", "ignore").lower() if m else "utf-8"
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    try:
        s = raw.decode(enc, "ignore")
    except LookupError:
        s = raw.decode("utf-8", "ignore")
    s = DROP.sub(" ", s)
    s = BLOCK.sub("\n", s)
    s = TAG.sub(" ", s)
    s = html.unescape(s)
    lines = [re.sub(r"[ \t\u3000]+", " ", ln).strip() for ln in s.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def fetch(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), (r.headers.get("Content-Type") or "").lower(), ""
    except Exception as e:  # noqa: BLE001
        return None, "", f"{type(e).__name__}:{e}"


def main() -> int:
    args = sys.argv[1:]
    urls = [a for a in args if a.startswith("http")]
    keys = [a for a in args if not a.startswith("http")]
    rc = 0
    for url in urls:
        rc |= scan(url, keys)
    return rc


def scan(url: str, keys: list) -> int:
    raw, ctype, err = fetch(url)
    if raw is None:
        print(f"[FAIL] {url} -> {err}")
        return 1
    if "pdf" in ctype:
        try:
            import io

            from pypdf import PdfReader

            rd = PdfReader(io.BytesIO(raw))
            text = "\n".join((p.extract_text() or "") for p in rd.pages)
        except Exception as e:  # noqa: BLE001
            print(f"[PDF-ERR] {e}")
            return 1
    else:
        text = to_text(raw)
    print(f"[OK] {url} ctype={ctype} chars={len(text)}")
    if not keys:
        print(text[:3000])
        return 0
    flat = re.sub(r"\s+", " ", text)
    seen, hits = set(), 0
    for k in keys:
        for m in re.finditer(re.escape(k), flat):
            lo, hi = max(0, m.start() - 120), min(len(flat), m.end() + 160)
            win = flat[lo:hi]
            if win in seen:
                continue
            seen.add(win)
            hits += 1
            print(f"--- [{k}] ---")
            print(win)
            if hits >= 12:
                break
        if hits >= 12:
            break
    print(f"[HITS] {hits} textlen={len(flat)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
