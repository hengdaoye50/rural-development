# -*- coding: utf-8 -*-
"""从政府网文章页抽取正文 → Markdown。
用法: python _zj03_art.py <url> <out.json> [slug]
输出 json: {url,title,body_md,issued_ymd,published_ymd,doc_no,issuer_hint,chars}
"""
import sys, re, json, importlib.util, html as htmlmod
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

CAND = [r'id="zoom"', r'id="zoomcon"', r'class="TRS_Editor"', r'class="[^"]*article[^"]*content',
        r'class="[^"]*content[^"]*"', r'id="content"', r'id="mainText"', r'class="[^"]*detail[^"]*']


def inner(html, start_idx, tag="div"):
    """从 start_idx 处的开标签开始，返回配对闭合的内部 HTML。"""
    depth = 1
    i = start_idx
    pat = re.compile(r"(?is)</?%s\b[^>]*>" % tag)
    while True:
        m = pat.search(html, i)
        if not m:
            return html[start_idx:]
        if m.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return html[start_idx:m.start()]
        else:
            depth += 1
        i = m.end()


def pick_body(h):
    best = None
    for c in CAND:
        m = re.search(r"(?is)<(div|td|article|section)[^>]*" + c + r"[^>]*>", h)
        if not m:
            continue
        tag = m.group(1)
        body = inner(h, m.end(), tag)
        txt = t.strip(body)
        n = len(re.findall(r"[\u4e00-\u9fff]", txt))
        if n > 120 and (best is None or n > best[0]):
            best = (n, body, tag)
    if best is None:
        body = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", h)
        return body
    return best[1]


def to_md(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", "", h)
    h = re.sub(r"(?is)<!--.*?-->", "", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    # tables
    def tbl(m):
        rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", m.group(0))
        out = []
        for i, r in enumerate(rows):
            cells = [t.strip(c).replace("\n", " ") for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", r)]
            if not any(cells):
                continue
            out.append("| " + " | ".join(cells) + " |")
            if i == 0:
                out.append("|" + "|".join(["---"] * len(cells)) + "|")
        return "\n\n" + "\n".join(out) + "\n\n"
    h = re.sub(r"(?is)<table[^>]*>.*?</table>", tbl, h)
    h = re.sub(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>", lambda m: "\n\n" + "#" * (int(m.group(1)) + 1) + " " + t.strip(m.group(2)).replace("\n", " ") + "\n\n", h)
    h = re.sub(r"(?is)</p>", "\n\n", h)
    h = re.sub(r"(?is)<p[^>]*>", "", h)
    h = re.sub(r"(?is)</div>", "\n\n", h)
    h = re.sub(r"(?is)<li[^>]*>", "\n- ", h)
    h = re.sub(r"(?s)<[^>]+>", "", h)
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&ldquo;", "“"), ("&rdquo;", "”"), ("&mdash;", "—"), ("&#39;", "'")]:
        h = h.replace(a, b)
    h = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), h)
    lines = [re.sub(r"[ \t\u3000]+", " ", l).strip() for l in h.split("\n")]
    out, blank = [], False
    for l in lines:
        if not l:
            if not blank and out:
                out.append("")
            blank = True
            continue
        blank = False
        out.append(l)
    return "\n".join(out).strip()


def clean_title(ht):
    m = re.search(r"(?is)<title>(.*?)</title>", ht)
    if not m:
        return ""
    s = t.strip(m.group(1))
    for sep in ["_", "－", "-", "|"]:
        pass
    return re.sub(r"[_\|].*$", "", s).strip()


def main():
    url, outp = sys.argv[1], sys.argv[2]
    ht = t.fetch(url)
    title = clean_title(ht)
    # 优先用页面内 h1/标题字段
    m = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', ht) or re.search(r'class="[^"]*(?:title|tit)[^"]*"[^>]*>(.*?)<', ht)
    if m:
        cand = t.strip(m.group(1)).replace("\n", " ")
        if 4 < len(cand) < 120 and "首页" not in cand:
            title = cand
    body = to_md(pick_body(ht))
    # 日期
    iss = pub = ""
    mp = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", ht)
    if mp:
        pub = f"{mp.group(1)}-{int(mp.group(2)):02d}-{int(mp.group(3)):02d}"
    mn = re.search(r"([\u4e00-\u9fff]{1,12}(?:发|办发|政发|厅发|委发|政办发|府办发))〔(20\d{2})〕(\d+)号", ht)
    doc_no = f"{mn.group(1)}〔{mn.group(2)}〕{mn.group(3)}号" if mn else ""
    chars = len(re.findall(r"[\u4e00-\u9fff]", body))
    json.dump({"url": url, "title": title, "body_md": body, "published_ymd": pub,
               "doc_no": doc_no, "chars": chars}, open(outp, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"OK chars={chars} title={title}")
    print(body[:200].replace("\n", " "))


if __name__ == "__main__":
    main()
