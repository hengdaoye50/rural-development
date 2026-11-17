"""抓取 `.gov.cn` 原文并生成 ingest_policy 可用的批次 JSONL。

解决一个具体摩擦：手采时「打开页面 → 复制正文 → 拼 JSONL → 算哈希」很容易出错，
而 ingest_policy 要求 full_text 完整、哈希按磁盘字节一致。本脚本把这几步串起来。

用法（每条一个 --doc，参数用 key=value，逗号分隔）：

    python scripts/fetch_gov_doc.py --out data/stage/batches/POL-SD-X-policy.jsonl \
      "url=http://nync.shandong.gov.cn/.../t20251231_4885019.html,
       title=山东省农业农村厅2025年重点任务公开承诺事项完成情况,
       issuer=山东省农业农村厅,issuer_level=province,doc_type=其他,
       source_kind=部门动态,published_ymd=2025-12-31,credibility=B"

约束：只接受 .gov.cn 域名（docs/07 白名单）；正文提取后校验中文字数，过短直接失败，
不生成残缺记录。`full_text` 由脚本从页面提取，不手工改写。

    python scripts/fetch_gov_doc.py --dry-run --doc "url=..." # 只打印提取结果
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MIN_CN = 150          # docs/07：full_text_chars < 150 触发 QA 警告
DROP_TAGS = re.compile(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", re.S | re.I)


def fetch(url: str) -> str:
    if ".gov.cn" not in urllib.parse.urlparse(url).netloc:
        raise ValueError(f"非 .gov.cn 域名，按 docs/07 拒绝：{url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        ct = r.headers.get("Content-Type", "") or ""
    m = re.search(r"charset=([\w-]+)", ct, re.I)
    encs = [m.group(1)] if m else []
    encs += ["utf-8", "gb18030"]
    for enc in encs:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "ignore")


def to_text(html: str) -> str:
    html = DROP_TAGS.sub(" ", html)
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", "", text)
    lines = [" ".join(l.split()) for l in text.split("\n")]
    lines = [l for l in lines if l]
    out, prev = [], None
    for l in lines:
        if l != prev:                 # 去相邻重复行（导航与标题常重复）
            out.append(l)
        prev = l
    return "\n".join(out)


def body_of(html: str, title: str) -> str:
    """先试正文容器；容器过短就整页去导航——政府站模板差异太大，单一正则不可靠。"""
    whole = to_text(html)
    for pat in (r'<div[^>]+(?:id|class)="[^"]*(?:content|article|zoom|TRS_Editor|pages_content)[^"]*"[^>]*>(.*?)</div>\s*(?:</div>|<div)',
                r'<div[^>]+class="view TRS_UEDITOR[^"]*"[^>]*>(.*?)</div>'):
        m = re.search(pat, html, re.S | re.I)
        if m:
            cand = to_text(m.group(1))
            if cn_chars(cand) >= MIN_CN:
                return cand
    # 兜底：从标题行之后截到页脚标记之前
    lines = whole.split("\n")
    start = 0
    for i, l in enumerate(lines):
        if title and title[:12] in l:
            start = i + 1
            break
    end = len(lines)
    for i in range(len(lines) - 1, start, -1):
        if re.search(r"(主办：|承办：|网站地图|ICP备|政府网站标识码)", lines[i]):
            end = i
            break
    trimmed = "\n".join(lines[start:end]).strip()
    return trimmed if cn_chars(trimmed) >= MIN_CN else whole


def cn_chars(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fa5]", s))


def parse_doc(spec: str) -> dict[str, str]:
    d = {}
    for part in spec.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        d[k.strip()] = v.strip()
    if "url" not in d:
        raise ValueError("缺少 url")
    return d


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    out_path = None
    if "--out" in argv:
        out_path = ROOT / argv[argv.index("--out") + 1]
    specs, i = [], 0
    while i < len(argv):
        if argv[i] == "--doc":
            specs.append(argv[i + 1])
            i += 2
        else:
            i += 1
    if not specs:
        print(__doc__)
        return 2

    rows = []
    for spec in specs:
        d = parse_doc(spec)
        url = d["url"]
        body = body_of(fetch(url), d.get("title", ""))
        n = cn_chars(body)
        print(f"  {d.get('title', url)[:40]}｜正文 {n} 汉字")
        if n < MIN_CN:
            print(f"  !! 正文仅 {n} 汉字，低于 {MIN_CN}，拒绝生成（不当摘录存库）")
            return 1
        row = {
            "url": url,
            "title": d.get("title", ""),
            "doc_no": d.get("doc_no", ""),
            "issuer": d.get("issuer", ""),
            "issuer_level": d.get("issuer_level", ""),
            "issued_ymd": d.get("issued_ymd", ""),
            "published_ymd": d.get("published_ymd", ""),
            "doc_type": d.get("doc_type", "其他"),
            "source_kind": d.get("source_kind", "部门动态"),
            "province_code": d.get("province_code", ""),
            "city_code": d.get("city_code", ""),
            "county_code": d.get("county_code", ""),
            "instruments": d.get("instruments", ""),
            "scope_desc": d.get("scope_desc", ""),
            "summary": d.get("summary", ""),
            "credibility": d.get("credibility", "B"),
            "slug": d.get("slug", ""),
            "areas": [],
            "events": [],
            "full_text": body,
        }
        rows.append(row)

    if dry:
        print("\ndry-run：不写盘")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"已写入 {len(rows)} 条 -> {out_path.relative_to(ROOT)}")
    print("接着跑：ingest_policy.py <该文件> -> merge -> build -> validate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
