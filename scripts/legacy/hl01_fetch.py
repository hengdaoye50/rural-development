"""HL01 批次一次性抓取器：url -> 正文 Markdown -> 追加到 POL-HL01-policy.jsonl。

不参与管线。只用标准库 + pypdf，避免给 MIMO_PYTHON 装依赖。

用法：
  python scripts/legacy/hl01_fetch.py probe URL [URL ...]      # 只看抓到的标题/字数/首尾
  python scripts/legacy/hl01_fetch.py add spec.json            # spec 为 [{...meta, url}] 列表
  python scripts/legacy/hl01_fetch.py add1 spec.json           # 单条调试
"""
from __future__ import annotations

import html as htmllib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "stage" / "batches" / "POL-HL01-policy.jsonl"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)
DROP_TAGS = {"script", "style", "noscript", "iframe", "form", "select", "svg", "button"}
BLOCK_TAGS = {"div", "p", "td", "th", "li", "tr", "section", "article", "table", "ul", "ol"}
BOILER = re.compile(
    r"^(扫一扫|打印本页|打印|关闭窗口|分享到|返回顶部|相关阅读|相关链接|关联稿件|上一篇|下一篇|"
    r"责任编辑|网站地图|主办单位|承办单位|主办：|承办：|技术支持|黑ICP|黑公网安备|"
    r"政府网站标识码|备案序号|版权所有|浏览量|访问量|点击量|【字体|【关闭|【打印|字号：|点赞|"
    r"TOP|文字解读|其他解读|政策解读|相关解读|解读：|图表解读|"
    r"索\s*引\s*号|发文字号：|文\s*号：|层\s*级：|主题分类：|主\s*题\s*词|发文机关：|"
    r"成文日期：|发布日期：|发文日期：|发布机构：|名\s*称：|时\s*效|分类：|有效性：|"
    r"来源：|作者：|关闭本页)"
)


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []
        self.parent = parent


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in ("br", "img", "meta", "link", "input", "hr", "source"):
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        node = self.cur
        while node is not self.root:
            if node.tag == tag:
                self.cur = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.children.append(data)


def text_of(node) -> str:
    if isinstance(node, str):
        return node
    if node.tag in DROP_TAGS:
        return ""
    return "".join(text_of(c) for c in node.children)


def cn_len(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5]", s))


CONTENT_HINT = re.compile(
    r"zoom|TRS_Editor|TRS_UEDITOR|Custom_UnionStyle|article|content|conTxt|xl_con|"
    r"wzcon|pages_content|zwnj|news_con|textCon|articleCon|zwxl|zw_con|detail|view\b|"
    r"conTxt|mainText|wz_content",
    re.I,
)


def find_content(root: Node) -> Node:
    """先按 id/class 提示定位正文容器，再退回「汉字数 - 链接惩罚」评分。

    不能给 body 加权：父级容器一旦把导航与正文一起收进来，加权会让整页都被选中。
    """
    hinted: list[tuple[int, Node]] = []
    scored: list[tuple[float, Node]] = []

    def walk(node):
        if isinstance(node, str) or node.tag in DROP_TAGS:
            return
        if node.tag not in ("div", "td", "article", "section", "main", "span"):
            for c in node.children:
                walk(c)
            return
        attrs = node.attrs
        marker = f"{attrs.get('id','')} {attrs.get('class','')}"
        n = cn_len(text_of(node))
        if n:
            if marker.strip() and CONTENT_HINT.search(marker):
                hinted.append((n, node))
            a_len = sum(cn_len(text_of(x)) for x in iter_tags(node, "a"))
            scored.append((n - 1.6 * a_len, node))
        for c in node.children:
            walk(c)

    walk(root)
    if hinted:
        hinted.sort(key=lambda x: -x[0])
        if hinted[0][0] >= 150:
            return hinted[0][1]
    if not scored:
        return root
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def iter_tags(node, tag):
    for c in node.children:
        if isinstance(c, str) or c.tag in DROP_TAGS:
            continue
        if c.tag == tag:
            yield c
        yield from iter_tags(c, tag)


def render(node) -> str:
    out: list[str] = []

    def emit(s: str):
        if s:
            out.append(s)

    def walk(n, inline: bool):
        if isinstance(n, str):
            emit(re.sub(r"[ \t\r\n\u3000]+", " ", n))
            return
        t = n.tag
        if t in DROP_TAGS:
            return
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            emit("\n\n## " + re.sub(r"\s+", " ", text_of(n)).strip() + "\n\n")
            return
        if t == "br":
            emit("\n")
            return
        if t == "tr":
            cells = [
                re.sub(r"\s+", " ", text_of(c)).strip()
                for c in n.children
                if not isinstance(c, str) and c.tag in ("td", "th")
            ]
            if cells:
                emit("\n| " + " | ".join(cells) + " |")
            return
        if t == "table":
            emit("\n")
            for c in n.children:
                walk(c, False)
            emit("\n\n")
            return
        if t in ("p", "div", "section", "article", "ul", "ol", "blockquote"):
            emit("\n\n")
            for c in n.children:
                walk(c, False)
            emit("\n\n")
            return
        if t == "li":
            emit("\n- ")
            for c in n.children:
                walk(c, True)
            return
        for c in n.children:
            walk(c, inline)

    walk(node, False)
    txt = "".join(out)
    lines = []
    for ln in txt.split("\n"):
        s = ln.strip()
        if not s:
            lines.append("")
            continue
        if BOILER.match(s):
            continue
        if cn_len(s) < 2 and not s.startswith(("-", "|", "#")):
            continue
        lines.append(s)
    txt = "\n".join(lines)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def decode(raw: bytes) -> str:
    m = re.search(rb'charset\s*=\s*["\']?([\w-]+)', raw[:4000], re.I)
    encs = []
    if m:
        e = m.group(1).decode("ascii", "ignore").lower()
        encs.append("gb18030" if e in ("gb2312", "gbk", "gb18030") else e)
    encs += ["utf-8", "gb18030"]
    for e in encs:
        try:
            return raw.decode(e)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "ignore")


def http_get(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read()
    except Exception as e:
        print(f"  [urllib 失败 {type(e).__name__}: {e}] 改用 curl.exe", file=sys.stderr)
    with tempfile.TemporaryDirectory() as td:
        dst = Path(td) / "f.bin"
        base = ["curl.exe", "-sSL", "--max-time", "60", "-A", UA, "-o", str(dst)]
        r = subprocess.run(base + [url], capture_output=True)
        if r.returncode != 0:
            # 部分县级站点证书主机名不匹配（站点自身配置错误），退回忽略校验并记录
            print(f"  [curl 失败 rc={r.returncode}，改用 -k 忽略证书校验]", file=sys.stderr)
            subprocess.run(base[:1] + ["-k"] + base[1:] + [url], check=True, capture_output=True)
        return dst.read_bytes()


def pdf_text(path_or_bytes, url: str) -> str:
    import io

    from pypdf import PdfReader

    data = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    rd = PdfReader(io.BytesIO(data))
    return "\n\n".join((p.extract_text() or "") for p in rd.pages)


def fetch(url: str, pdf_out: Path | None = None) -> tuple[str, str]:
    raw = http_get(url)
    if raw[:4] == b"%PDF" or url.lower().endswith(".pdf"):
        if pdf_out:
            pdf_out.parent.mkdir(parents=True, exist_ok=True)
            pdf_out.write_bytes(raw)
        txt = pdf_text(raw, url)
        body = re.sub(r"\n{3,}", "\n\n", txt).strip()
        return "", body
    doc = decode(raw)
    tb = TreeBuilder()
    tb.feed(doc)
    m = re.search(r"<title[^>]*>(.*?)</title>", doc, re.S | re.I)
    page_title = htmllib.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else ""
    body = render(find_content(tb.root))
    return page_title, body


def probe(urls):
    for u in urls:
        try:
            t, b = fetch(u)
        except Exception as e:
            print(f"\n### {u}\n  FAIL {type(e).__name__}: {e}")
            continue
        print(f"\n### {u}\n  title={t!r}\n  cn={cn_len(b)} len={len(b)}")
        print("  HEAD:", re.sub(r"\s+", " ", b[:180]))
        print("  TAIL:", re.sub(r"\s+", " ", b[-160:]))


def load_spec(p: Path) -> list[dict]:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def add(spec_path: Path, only_one: bool = False):
    recs = load_spec(spec_path)
    if only_one:
        recs = recs[:1]
    done = 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = OUT.read_text(encoding="utf-8").splitlines() if OUT.exists() else []
    have_urls = set()
    for ln in existing:
        if ln.strip():
            try:
                have_urls.add(json.loads(ln).get("url", ""))
            except json.JSONDecodeError:
                pass
    for r in recs:
        url = r["url"]
        if url in have_urls:
            print(f"  已有，跳过 {url}")
            continue
        slug = r.get("slug") or "hl01-doc"
        pdf_out = ROOT / "data" / "raw" / "HL" / f"_tmp-{slug}" / "原件.pdf"
        try:
            page_title, body = fetch(url, pdf_out)
        except Exception as e:
            print(f"  !! 抓取失败 {url} :: {type(e).__name__}: {e}")
            continue
        n = cn_len(body)
        if n < 150:
            print(f"  !! 正文过短({n}字) 不入库 {url}")
            continue
        if page_title and not r.get("_page_title"):
            r["_page_title"] = page_title
        r["full_text"] = body
        r.pop("_page_title", None)
        line = json.dumps(r, ensure_ascii=False)
        with OUT.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
        have_urls.add(url)
        done += 1
        print(f"  + {n:5d}字  {r.get('title','')[:44]}")
        if pdf_out.exists() and not r.get("_keep_pdf"):
            pdf_out.unlink(missing_ok=True)
    print(f"追加 {done} 条 -> {OUT}")


def scan(urls, kws):
    for u in urls:
        try:
            t, b = fetch(u)
        except Exception as e:
            print(f"\n### {u}\n  FAIL {type(e).__name__}: {e}")
            continue
        print(f"\n### {u}\n  title={t!r}  cn={cn_len(b)}")
        hits = 0
        for ln in b.split("\n"):
            if any(k in ln for k in kws):
                hits += 1
                print("   >", ln[:260])
                if hits >= 14:
                    print("   ... (截断)")
                    break
        if not hits:
            print("   (无关键词命中)")


def links(url, base_filter=""):
    """列栏目页的标题+链接，用于枚举政策文件列表。"""
    raw = http_get(url)
    doc = decode(raw)
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', doc, re.S | re.I):
        href, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        txt = htmllib.unescape(re.sub(r"\s+", " ", txt)).strip()
        if cn_len(txt) < 5:
            continue
        if base_filter and base_filter not in href:
            continue
        print(f"  {txt[:60]}\n      {href}")


def dates(urls):
    """列出页面里出现的日期串，用于判定 published_ymd / issued_ymd。"""
    for u in urls:
        try:
            doc = decode(http_get(u))
        except Exception as e:
            print(f"\n### {u}\n  FAIL {type(e).__name__}: {e}")
            continue
        found = []
        for m in re.finditer(r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}日?", doc):
            s = m.group(0)
            if s not in found:
                found.append(s)
        ctx = []
        for kw in ("发布日期", "发布时间", "成文日期", "发文日期", "信息形成", "公开日期", "文号", "发文字号"):
            for m in re.finditer(kw + r"[^<>\n]{0,40}", doc):
                t = re.sub(r"\s+", " ", m.group(0)).strip()
                if t not in ctx:
                    ctx.append(t)
        print(f"\n### {u}")
        print("  dates:", " ".join(found[:12]))
        print("  ctx:", " | ".join(ctx[:8]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "probe":
        probe(sys.argv[2:])
    elif cmd == "dates":
        dates(sys.argv[2:])
    elif cmd == "scan":
        KW = ["示范带", "片区", "示范区", "示范村", "和美乡村", "精品村", "乡村振兴示范",
              "组团", "联建", "抱团"]
        scan(sys.argv[2:], KW)
    elif cmd == "links":
        links(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif cmd == "add":
        add(Path(sys.argv[2]))
    elif cmd == "add1":
        add(Path(sys.argv[2]), only_one=True)
    else:
        print(__doc__)
