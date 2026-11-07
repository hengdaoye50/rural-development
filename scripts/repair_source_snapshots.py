"""补采失效来源的原文快照。

对 source 表中 local_path 指向不存在文件的记录：
  - URL 可访问 → 抓原文、存 原件 + 原文.md + meta.json、算哈希、更新 local_path/hash_sha256
  - URL 已死   → 清空 local_path/hash_sha256（不留虚假的「已存档」标记），记入报告

local_path 统一规范为 `data/raw/{ABBR}/{日期}-{slug}/原文.md`。

用法：
  python scripts/repair_source_snapshots.py --dry-run
  python scripts/repair_source_snapshots.py --limit 10
  python scripts/repair_source_snapshots.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
CLEAN = ROOT / "data" / "clean"
BY_PROV = CLEAN / "by_province"
REPORT = ROOT / "reports" / "qa"

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


def fetch(url: str, timeout: int = 25) -> tuple[bytes | None, str, str]:
    """返回 (内容, content_type, 错误说明)。"""
    if not url.startswith("http"):
        return None, "", "非 http URL"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), (r.headers.get("Content-Type") or "").lower(), ""
    except urllib.error.HTTPError as e:
        return None, "", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, "", type(e).__name__


def pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(raw))
        return "\n".join((pg.extract_text() or "") for pg in rd.pages)
    except Exception:  # noqa: BLE001
        return ""


def canonical_dir(local_path: str) -> Path:
    """把现有 local_path（目录形式或 .md 形式）统一成目录。"""
    p = Path(local_path)
    return p.parent if p.suffix.lower() in (".md", ".html", ".htm", ".pdf") else p


def slug_from(title: str, fallback: str) -> str:
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9]+", "-", title or "").strip("-")
    return (s[:40] or fallback)


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") or "" for h in header})


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    limit = 0
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    targets = [
        r for r in conn.execute(
            "select source_id, url, title, publisher, published_ymd, fetched_at, "
            "credibility, local_path from source"
        )
        if r["local_path"] and not os.path.exists(r["local_path"])
    ]
    if limit:
        targets = targets[:limit]

    # 定位每个 source_id 落在哪个 by_province 文件
    owner: dict[str, tuple[Path, list[str], list[dict]]] = {}
    for p in sorted(BY_PROV.glob("*-source.csv")):
        header, rows = _read(p)
        if not header:
            continue
        idx = {r.get("source_id"): r for r in rows}
        for r in targets:
            if r["source_id"] in idx:
                owner[r["source_id"]] = (p, header, rows)

    print(f"待修复 {len(targets)} 条；已定位所属文件 {len(owner)} 条")
    recovered, failed, empty = [], [], []

    for i, r in enumerate(targets, 1):
        sid = r["source_id"]
        if sid not in owner:
            failed.append((sid, "未找到所属 by_province 文件"))
            continue
        content, ctype, err = fetch(r["url"])
        time.sleep(0.3)
        if content is None:
            failed.append((sid, err))
            print(f"  [{i}/{len(targets)}] {sid} 失败: {err}")
            continue

        is_pdf = "pdf" in ctype or r["url"].lower().endswith(".pdf")
        text = pdf_text(content) if is_pdf else to_text(content)
        text = text.strip()

        d = canonical_dir(r["local_path"])
        md_path = d / "原文.md"
        rel = md_path.as_posix()
        body = f"# {r['title']}\n\n{text}\n" if text else f"# {r['title']}\n\n（原文抓取成功但正文提取为空，原件已保存）\n"
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()

        if not dry:
            d.mkdir(parents=True, exist_ok=True)
            (d / ("原件.pdf" if is_pdf else "原件.html")).write_bytes(content)
            md_path.write_text(body, encoding="utf-8", newline="\n")
            import json
            (d / "meta.json").write_text(json.dumps({
                "source_id": sid, "url": r["url"], "title": r["title"],
                "publisher": r["publisher"], "published_ymd": r["published_ymd"],
                "fetched_at": time.strftime("%Y-%m-%d"),
                "cred": r["credibility"],
                "recovered": True, "note": "补采：原快照缺失，2026-10 重新抓取",
                "text_chars": len(text),
            }, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

            _, header, rows = owner[sid]
            for row in rows:
                if row.get("source_id") == sid:
                    row["local_path"] = rel
                    row["hash_sha256"] = sha
                    break

        if len(text) < 100:
            empty.append((sid, len(text), r["url"]))
        recovered.append((sid, len(text), r["credibility"]))
        if i % 10 == 0:
            print(f"  {i}/{len(targets)} 已恢复 {len(recovered)}")

    # 死链：清空 local_path/hash，不留虚假存档标记
    if not dry:
        for sid, _reason in failed:
            if sid not in owner:
                continue
            _, header, rows = owner[sid]
            for row in rows:
                if row.get("source_id") == sid:
                    row["local_path"] = ""
                    row["hash_sha256"] = ""
                    break
        for p, header, rows in {v[0]: v for v in owner.values()}.values():
            _write(p, header, rows)

    print(f"\n{'[dry-run] ' if dry else ''}恢复 {len(recovered)} 条，失败 {len(failed)} 条")
    if empty:
        print(f"其中正文提取不足 100 字 {len(empty)} 条（原件已保存，可能需要渲染）：")
        for sid, n, u in empty[:10]:
            print(f"  {sid} {n} 字  {u[:70]}")
    if failed:
        print("无法恢复：")
        for sid, reason in failed:
            print(f"  {sid}  {reason}")

    if not dry and (recovered or failed):
        REPORT.mkdir(parents=True, exist_ok=True)
        out = REPORT / "source-snapshot-repair.csv"
        with out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["source_id", "result", "detail"])
            for sid, n, cred in recovered:
                w.writerow([sid, "recovered", f"{n} 字 / {cred}"])
            for sid, reason in failed:
                w.writerow([sid, "failed", reason])
        print(f"\n-> {out}")
        print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
