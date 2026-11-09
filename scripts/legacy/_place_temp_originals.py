"""一次性：把临时目录里未归档的原件归位到 data/raw/{ABBR}/{日期}-{slug}/原件.pdf。

不靠文件名猜，按内容比对：从 policy 的 full_text 取一段去空白的特征片段，
在 PDF/DOC 抽出的文本里查这段是否出现，命中即认定同一份文件。

用法：
  python scripts/legacy/_place_temp_originals.py --dry-run
  python scripts/legacy/_place_temp_originals.py
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TEMP_DIRS = [ROOT / "data" / "stage" / "batches", ROOT / "tmp"]
PROV_FILTER = ("LN", "QH", "JX")
WS = re.compile(r"\s+")


def norm(s: str) -> str:
    return WS.sub("", s)


def pdf_text(p: Path) -> str:
    try:
        from pypdf import PdfReader

        r = PdfReader(str(p))
        return "\n".join((pg.extract_text() or "") for pg in r.pages)
    except Exception as e:  # noqa: BLE001
        print(f"    抽文本失败 {p.name}: {e}")
        return ""


def doc_text(p: Path) -> str:
    soffice = None
    for cand in (r"C:\Program Files\LibreOffice\program\soffice.exe",):
        if Path(cand).exists():
            soffice = cand
            break
    if not soffice:
        print("    找不到 soffice，跳过 .doc")
        return ""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            [soffice, "--headless", "--norestore",
             f"-env:UserInstallation=file:///{td.replace(chr(92), '/')}/p",
             "--convert-to", "txt:Text", "--outdir", td, str(p)],
            capture_output=True, timeout=300,
        )
        out = Path(td) / (p.stem + ".txt")
        if not out.exists():
            return ""
        return out.read_bytes().decode("gb18030", "replace")


def samples(text: str, k: int = 3) -> list[str]:
    """从正文取几段去空白的特征片段（避开标题行）。"""
    body = text.split("\n", 1)[-1]
    n = norm(body)
    if len(n) < 200:
        return []
    out = []
    for frac in (0.25, 0.5, 0.75):
        i = int(len(n) * frac)
        out.append(n[i: i + 50])
    return [s for s in out if len(s) == 50][:k]


def main() -> int:
    dry = "--dry-run" in sys.argv
    conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
    conn.row_factory = sqlite3.Row
    pols = []
    for abbr in PROV_FILTER:
        for r in conn.execute(
            "SELECT policy_id, province_code, local_path, title FROM policy "
            "WHERE SUBSTR(local_path, 10, 2) = ?", (abbr,)
        ):
            lp = ROOT / r["local_path"]
            if lp.exists():
                pols.append((r["policy_id"], r["local_path"], lp.read_text(encoding="utf-8")))
    print(f"候选 policy {len(pols)} 条（{'/'.join(PROV_FILTER)}）\n")

    placed = 0
    unmatched = []
    for d in TEMP_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in {".pdf", ".doc"}:
                continue
            if p.stat().st_size == 0:
                print(f"空文件跳过：{p.relative_to(ROOT)}")
                continue
            rel = p.relative_to(ROOT)
            txt = pdf_text(p) if p.suffix.lower() == ".pdf" else doc_text(p)
            nt = norm(txt)
            if len(nt) < 200:
                unmatched.append((rel, "无可抽文本"))
                print(f"?? 无可抽文本：{rel}")
                continue
            hit = None
            for pid, local_path, body in pols:
                ss = samples(body)
                score = sum(1 for s in ss if s in nt)
                if score >= 2:
                    hit = (pid, local_path, score)
                    break
            if not hit:
                unmatched.append((rel, "内容无匹配（可能是未入库的扫描件）"))
                print(f"?? 内容无匹配：{rel}")
                continue
            pid, local_path, score = hit
            target = (ROOT / local_path).parent / "原件.pdf"
            print(f"-> {rel}\n     = {pid}  {target.relative_to(ROOT)}  (命中 {score}/3)")
            if not dry:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
            placed += 1

    print(f"\n{'dry-run，' if dry else ''}归位 {placed} 份，未匹配 {len(unmatched)} 份")
    for m, why in unmatched:
        print("  未匹配：", m, "—", why)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
