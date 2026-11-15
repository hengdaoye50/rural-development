"""临时：按 spec 抓全文 -> 抽元数据 -> 追加 JSONL（不参与管线）。

用法：
  python scripts/legacy/_tmp_build.py preview https://xxx.html
  python scripts/legacy/_tmp_build.py build spec.json out.jsonl
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CONTAINERS = [
    ".xxgk-wzcon", ".wzcon", ".j-fontContent", "#zoom", ".TRS_Editor",
    "#content", ".content_detail", ".article-content", ".zwcon",
    ".wznr", "#xl_cont", ".detail-content", ".article",
]
DATE_RE = re.compile(r"(20\d\d)[-年/](\d{1,2})[-月/](\d{1,2})")


def fetch(url: str, timeout: int = 30) -> str:
    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout).read()
    m = re.search(rb'charset=["\']?([\w-]+)', raw[:4000], re.I)
    enc = (m.group(1).decode("ascii", "ignore").lower() if m else "utf-8")
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    try:
        return raw.decode(enc, "ignore")
    except LookupError:
        return raw.decode("utf-8", "ignore")


def pick_container(soup):
    for sel in CONTAINERS:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 200:
            return node, sel
    best, best_len = None, 0
    for node in soup.find_all(["div", "td", "article", "section"]):
        txt = node.get_text(strip=True)
        if len(txt) > best_len:
            best, best_len = node, len(txt)
    return best, f"fallback:{best.name if best else None}"


def to_md(node) -> str:
    for bad in node.select("script,style,noscript,.share,.fj,.print"):
        bad.decompose()
    out = []
    for el in node.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"], recursive=True):
        if el.name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
                if any(cells):
                    rows.append(cells)
            if rows:
                out.append("")
                out.append("| " + " | ".join(rows[0]) + " |")
                out.append("|" + "---|" * len(rows[0]))
                for r in rows[1:]:
                    r = r + [""] * (len(rows[0]) - len(r))
                    out.append("| " + " | ".join(r) + " |")
                out.append("")
            continue
        if el.find("table") and el.name != "table":
            continue
        txt = el.get_text("\n", strip=True)
        txt = re.sub(r"\n{2,}", "\n", txt).strip()
        if not txt:
            continue
        if el.name in ("h1", "h2", "h3", "h4"):
            out.append(f"## {txt}")
        elif el.name == "li":
            out.append(f"- {txt}")
        else:
            out.append(txt)
    text = "\n\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def meta(soup, html: str):
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    if not title:
        t = soup.find("title")
        title = t.get_text(" ", strip=True) if t else ""
    m = re.search(r"来源[：:]\s*([^\s<　]{2,40})", html)
    source = m.group(1) if m else ""
    m = re.search(r"(?:发布时间|发布日期|时间)[：:]\s*(20\d\d-\d\d-\d\d(?:\s+\d\d:\d\d)?)", html)
    pub = m.group(1) if m else ""
    if not pub:
        d = DATE_RE.findall(html)
        pub = "-".join([d[0][0], d[0][1].zfill(2), d[0][2].zfill(2)]) if d else ""
    return title, source, pub


def cn_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", re.sub(r"[#*|\-]", "", text)))


def pdf_to_md(text: str) -> str:
    text = re.sub(r"汨罗市人民政府公报\s*\d{4}\s*年第\s*\d+\s*期", "", text)
    text = re.sub(r"^\s*-\s*\d+\s*-\s*$", "", text, flags=re.M)
    flat = re.sub(r"\s*\n\s*", "", text)
    sents = [s for s in re.split(r"(?<=[。！？；])", flat) if s.strip()]
    paras, buf = [], []
    for s in sents:
        buf.append(s)
        if len(buf) >= 3:
            paras.append("".join(buf))
            buf = []
    if buf:
        paras.append("".join(buf))
    return "\n\n".join(paras).strip()


def load_doc(url: str):
    """返回 (body_md, title, source, pub)。PDF 走 pypdf。"""
    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40)
    ctype = (raw.headers.get("Content-Type") or "").lower()
    data = raw.read()
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        import io

        from pypdf import PdfReader

        rd = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in rd.pages)
        return pdf_to_md(text), "", "", ""
    m = re.search(rb'charset=["\']?([\w-]+)', data[:4000], re.I)
    enc = (m.group(1).decode("ascii", "ignore").lower() if m else "utf-8")
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    html = data.decode(enc, "ignore")
    soup = BeautifulSoup(html, "html.parser")
    title, source, pub = meta(soup, html)
    node, sel = pick_container(soup)
    return (to_md(node) if node else ""), title, source, pub


def preview(url: str) -> None:
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    title, source, pub = meta(soup, html)
    node, sel = pick_container(soup)
    body = to_md(node) if node else ""
    print(f"[URL] {url}")
    print(f"[TITLE] {title}")
    print(f"[SOURCE] {source}   [PUB] {pub}")
    print(f"[CONTAINER] {sel}  [BODY_CHARS] {cn_chars(body)}")
    print("[HEAD]", body[:700].replace("\n", " / "))
    print("[TAIL]", body[-500:].replace("\n", " / "))
    for d in re.findall(r"(在[^。]{0,60}会议上)", body)[:3]:
        print("[MEET]", d)
    print()


def build(spec_path: str, out_path: str) -> None:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing.add(json.loads(line)["url"])
    added = 0
    with out.open("a", encoding="utf-8", newline="\n") as f:
        for rec in spec:
            url = rec["url"]
            if url in existing:
                print(f"[SKIP-EXISTS] {url}")
                continue
            body, title, source, pub = load_doc(url)
            for marker in rec.get("cut_at") or []:
                if marker in body:
                    body = body[: body.index(marker)].rstrip()
            title = rec.get("title") or title
            if cn_chars(body) < 150:
                print(f"[FAIL-BODY] {url} chars={cn_chars(body)}")
                continue
            row = {
                "title": title,
                "doc_no": rec.get("doc_no", ""),
                "issuer": rec.get("issuer") or source or "",
                "issuer_level": rec["issuer_level"],
                "issued_ymd": rec.get("issued_ymd", ""),
                "published_ymd": rec.get("published_ymd") or pub[:10],
                "doc_type": rec["doc_type"],
                "source_kind": rec["source_kind"],
                "province_code": "430000",
                "city_code": rec["city_code"],
                "county_code": rec["county_code"],
                "instruments": rec.get("instruments", ""),
                "scope_desc": rec.get("scope_desc", ""),
                "target_areas": rec.get("target_areas", ""),
                "budget_wan": rec.get("budget_wan", ""),
                "valid_state": rec.get("valid_state", "现行有效"),
                "url": url,
                "credibility": rec["credibility"],
                "summary": rec.get("summary", ""),
                "slug": rec["slug"],
                "fetched_at": rec.get("fetched_at", "2026-11-09"),
                "areas": rec["areas"],
                "events": rec.get("events", []),
                "full_text": body,
                "full_text_chars": cn_chars(body),
                "record_state": "active",
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            added += 1
            print(f"[ADD] {row['title'][:40]} chars={row['full_text_chars']} sel={sel}")
    print(f"[DONE] added={added} out={out}")


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        for u in sys.argv[2:]:
            preview(u)
    else:
        build(sys.argv[2], sys.argv[3])
