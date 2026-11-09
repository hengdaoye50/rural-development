"""一次性：临时目录里的扫描件原件归位（显式映射表，归属已逐份核对）。

依据 docs/03-采集规范 §3.1「原件必存」：原件为 PDF 的来源必须在 raw 目录同时留 `原件.pdf`。
归属核对方式：OCR 首页取标题/文号，与库内 policy 标题比对（见会话记录）。

用法：
  python scripts/legacy/_place_originals_explicit.py --dry-run
  python scripts/legacy/_place_originals_explicit.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 已入库记录的原件：临时路径 -> policy 的 local_path
TO_POLICY = {
    "data/stage/batches/_ln_tmp1.pdf":
        "data/raw/LN/20230426-ln-sheng-nongwei-2023-shifandai-mingdan/原文.md",
    "data/stage/batches/_ln_wfd_fj.doc":
        "data/raw/LN/20230830-ln-dl-wfd-wangdian-maquan-shifandai-guihua/原文.md",
    "data/stage/batches/_ln_zh2025.pdf":
        "data/raw/LN/2025-ln-dl-zh-2025-zhengfu-gongzuo-baogao/原文.md",
    "tmp/qh01/dt-zjxz2025.pdf":
        "data/raw/QH/202504-datong-2025-yangjie-zijin-xiada-tongzhi/原文.md",
    "tmp/qh01/dt-gtgh.pdf":
        "data/raw/QH/20260108-datong-guotu-kongjian-zongti-guihua-2021-2035/原文.md",
    "tmp/qh01/dt2024hmxc.doc":
        "data/raw/QH/20240416-datong-2024-hemeixiangcun-jianshe-xiangmu-shishifangan/原文.md",
}

# 相关但尚未入库的扫描件：合并到既有待补采目录，并登记进 gaps 清单
TO_PENDING = {
    "data/stage/batches/ocr-src/jx-gz-dy-sirongyigong-hemeixiangcun-gongzuofangan.pdf":
        "jx-dy-sirongyigong-hemeixiangcun-gongzuofangan.pdf",
    "data/stage/batches/_ln02_txt/ln155_pdf.pdf":
        "ln-sheng-shisuwu-guihua-gangyao-2026.pdf",
    "tmp/qh01/dt-tz2024b.pdf":
        "qh-datong-dacai-2024-384-jiexu-zijin-tiaozheng.pdf",
}
PENDING_DIR = "data/stage/batches/ocr-src"

# 与片区化无关（农村供水工程）或空文件，直接丢弃
DROP = [
    "tmp/qh01/dt-cz2026.pdf",
    "tmp/qh01/hy-dahua.pdf",
    "tmp/qh01/dt-gs2026.pdf",
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    placed = pending = dropped = 0

    for src_rel, local_path in TO_POLICY.items():
        src = ROOT / src_rel
        if not src.exists():
            print(f"跳过（不存在）：{src_rel}")
            continue
        body = ROOT / local_path
        if not body.exists():
            print(f"!! 目标 raw 目录缺 原文.md，拒绝写入：{local_path}")
            continue
        ext = src.suffix.lower()
        dst = body.parent / f"原件{ext}"
        print(f"原件归位 {src_rel}\n     -> {dst.relative_to(ROOT)}")
        if not dry:
            shutil.copy2(src, dst)
        placed += 1

    for src_rel, name in TO_PENDING.items():
        src = ROOT / src_rel
        if not src.exists():
            print(f"跳过（不存在）：{src_rel}")
            continue
        dst = ROOT / PENDING_DIR / name
        if src.resolve() == dst.resolve():
            print(f"已在待补采目录：{name}")
            continue
        print(f"待补采归档 {src_rel}\n     -> {dst.relative_to(ROOT)}")
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        pending += 1

    for src_rel in DROP:
        src = ROOT / src_rel
        if src.exists():
            print(f"丢弃 {src_rel}（空文件或与片区化无关）")
            if not dry:
                src.unlink()
            dropped += 1

    print(f"\n{'dry-run，' if dry else ''}归位 {placed} / 待补采 {pending} / 丢弃 {dropped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
