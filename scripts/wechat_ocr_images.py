# -*- coding: utf-8 -*-
"""公众号文章取图 + OCR：把名单长图识别成文本。

为什么需要：公众号名单常以「长图」发布（如山东第五批 102 个片区），
纯文本抓取只有数量。本脚本用 opencli 读页面 img，下载大图，再用 .venv-ocr 的 rapidocr 识别。

用法：
  python scripts/wechat_ocr_images.py --url "<mp.weixin URL>" --abbr SD
  python scripts/wechat_ocr_images.py --url "..." --min-height 600 --keep 6
产出：
  data/raw/{ABBR}/{date}-wx-img-{slug}/img-01.jpg ... + ocr.md + meta.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = "node"
MAIN_JS = str(Path(os.path.expandvars(r"%USERPROFILE%")) /
              r"scoop\apps\nodejs-lts\current\bin\node_modules\@jackwener\opencli\dist\src\main.js")
PY_OCR = ROOT / ".venv-ocr" / "Scripts" / "python.exe"


def cli(*args: str) -> str:
    r = subprocess.run([NODE, MAIN_JS, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return r.stdout or ""


def slug(s: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", s or "").strip("-")
    return (s or "wx")[:40]


def ocr(img: Path) -> str:
    """用 rapidocr 识别单张图。"""
    code = (
        "import sys,json\n"
        "from rapidocr_onnxruntime import RapidOCR\n"
        "r=RapidOCR()\n"
        "res,_=r(sys.argv[1])\n"
        "print(json.dumps([x[1] for x in (res or [])],ensure_ascii=False))\n"
    )
    r = subprocess.run([str(PY_OCR), "-c", code, str(img)], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    try:
        lines = json.loads((r.stdout or "").strip() or "[]")
    except Exception:  # noqa: BLE001
        return ""
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--abbr", default="WX")
    ap.add_argument("--min-height", type=int, default=600, help="只 OCR 高度≥该值的图（长图才是名单）")
    ap.add_argument("--keep", type=int, default=8)
    args = ap.parse_args()

    cli("browser", "main", "open", args.url, "--window", "background")
    time.sleep(5)   # 公众号页面异步渲染，太快拿到的是壳
    title = ""
    js = ("JSON.stringify(Array.from(document.querySelectorAll('img'))"
          ".map(function(i){return i.dataset.src||i.src;})"
          ".filter(function(s){return s && s.indexOf('mmbiz')>=0;}))")
    raw = cli("browser", "main", "eval", js)
    m = re.search(r"\[.*\]", raw, re.S)
    urls = json.loads(m.group(0)) if m else []
    imgs = [{"s": u} for u in urls]
    state = cli("browser", "main", "extract")
    mt = re.search(r'"title":\s*"([^"]*)"', state)
    title = mt.group(1) if mt else "wx"
    print(f"标题：{title}｜候选长图 {len(imgs)} 张")

    if not imgs:
        print("没有可 OCR 的长图（可能是纯文本文章）")
        return 0

    d = ROOT / "data" / "raw" / args.abbr / f"{date.today():%Y%m%d}-wx-img-{slug(title)}"
    d.mkdir(parents=True, exist_ok=True)
    texts = []
    for i, im in enumerate(imgs[: args.keep], 1):
        src = im["s"]
        ext = ".jpg"
        f = d / f"img-{i:02d}{ext}"
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://mp.weixin.qq.com/"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                f.write_bytes(resp.read())
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ 图 {i} 下载失败 {type(e).__name__}")
            continue
        if f.stat().st_size < 30 * 1024:   # 装饰小图跳过
            f.unlink(missing_ok=True)
            print(f"  - 图 {i} 过小，跳过")
            continue
        t = ocr(f)
        print(f"  ✓ 图 {i} {f.stat().st_size//1024}KB -> OCR {len(t)} 字")
        if t:
            texts.append(f"\n\n## 图 {i}\n\n{t}")
    if texts:
        (d / "ocr.md").write_text("".join(texts).strip(), encoding="utf-8", newline="\n")
        (d / "meta.json").write_text(json.dumps({
            "url": args.url, "title": title, "source_kind": "公众号图片OCR",
            "abbr": args.abbr, "fetched_at": date.today().isoformat(),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("OK ->", (d / "ocr.md").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
