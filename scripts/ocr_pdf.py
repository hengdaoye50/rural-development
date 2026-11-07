"""把扫描件 PDF 转成可入库的 Markdown 全文。

用于「PDF 是图片、pypdf 抽 0 字符」的来源补采：下载或读取 PDF →
逐页渲染成位图 → RapidOCR 识别 → 写 原文.md。

**必须用 OCR 专用环境跑**（项目根 `.venv-ocr`），不能用 MIMO_PYTHON：
    .venv-ocr\\Scripts\\python.exe scripts/ocr_pdf.py <pdf路径或URL> [选项]

例：
    .venv-ocr\\Scripts\\python.exe scripts/ocr_pdf.py https://x.gov.cn/a.pdf `
        --out "data/raw/JX/2024-dy-sirongyigong/原文.md"
    .venv-ocr\\Scripts\\python.exe scripts/ocr_pdf.py 原件.pdf --pages 1-3 --dry-run

选项：
    --out PATH        输出 Markdown（缺省写到 PDF 同目录的 原文.md）
    --scale N         渲染倍率，缺省 2.0；小字模糊时提到 3.0
    --pages A-B       只处理指定页段（1 起），缺省全部
    --dry-run         只识别并打印摘要，不写文件
    --min-chars N     单页少于此字数时告警，缺省 20

注意：OCR 不是无损的。实测会把「〔2024〕」识别成全角括号、把「五好两宜」偶尔认成
「五好两宣」。入库前应对文号、专有名词做抽样校读；`hash_sha256` 应按最终写入的
字节计算。
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

try:
    import numpy as np
    import pypdfium2 as pdfium
    from rapidocr_onnxruntime import RapidOCR
except ImportError as exc:  # pragma: no cover - 环境缺失时给出可操作提示
    print(f"缺少依赖：{exc}\n请用 .venv-ocr\\Scripts\\python.exe 运行本脚本", file=sys.stderr)
    raise SystemExit(3)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str, timeout: int = 120) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = Path(tempfile.gettempdir()) / f"ocr-{hashlib.md5(url.encode()).hexdigest()[:10]}.pdf"
    with urllib.request.urlopen(req, timeout=timeout) as resp, tmp.open("wb") as f:
        f.write(resp.read())
    return tmp


def parse_pages(spec: str, total: int) -> tuple[int, int]:
    if "-" in spec:
        a, b = spec.split("-", 1)
        start, end = int(a), int(b)
    else:
        start = end = int(spec)
    start = max(1, start)
    end = min(total, end)
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="PDF 本地路径或 http(s) URL")
    ap.add_argument("--out")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--pages")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-chars", type=int, default=20)
    ap.add_argument("--no-fix", action="store_true", help="跳过文号/专名纠错层")
    args = ap.parse_args()

    is_url = args.source.lower().startswith(("http://", "https://"))
    pdf_path = fetch(args.source) if is_url else Path(args.source)
    if not pdf_path.exists():
        print(f"找不到 {pdf_path}", file=sys.stderr)
        return 1

    out = Path(args.out) if args.out else pdf_path.with_name("原文.md")
    doc = pdfium.PdfDocument(str(pdf_path))
    total = len(doc)
    start, end = parse_pages(args.pages, total) if args.pages else (1, total)
    print(f"{pdf_path.name}  共 {total} 页，处理第 {start}–{end} 页，倍率 {args.scale}")

    ocr = RapidOCR()
    chunks: list[str] = []
    thin: list[int] = []
    for pno in range(start - 1, end):
        pil = doc[pno].render(scale=args.scale).to_pil()
        result, _ = ocr(np.array(pil))
        # 每个 box 是一行；用换行连接，保留版式线索且不丢字
        page_text = "\n".join(t for _, t, _ in (result or []))
        chunks.append(f"<!-- 第 {pno + 1} 页 -->\n{page_text}")
        n = len(page_text.replace("\n", ""))
        if n < args.min_chars:
            thin.append(pno + 1)
        print(f"  第 {pno + 1} 页：{n} 字")

    body = "\n\n".join(chunks).rstrip() + "\n"

    if not args.no_fix:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from ocr_normalize import load_terms, normalize

        body, changes = normalize(body, load_terms())
        if changes:
            print(f"  纠错 {len(changes)} 处：")
            for kind, old, new in changes:
                print(f"    [{kind}] {old}  ->  {new}")

    chars = len(body.replace("\n", ""))
    print(f"合计 {chars} 字")
    if thin:
        print(f"  !! 正文偏少的页（可能空白页或渲染不清，建议提高 --scale 重跑）：{thin}")

    if args.dry_run:
        print("dry-run：未写盘")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    print(f"OK: {out}  sha256={hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
