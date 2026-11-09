"""一次性：检查临时目录里的 PDF/DOC 是否已在 data/raw 归档（按文件内容哈希比对）。

项目约定「原件必存」：原件应落在 data/raw/{ABBR}/{日期}-{slug}/原件.pdf。
若某份原件只存在于临时目录，删临时目录前必须先归档。
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TEMP_DIRS = [ROOT / "data" / "stage" / "batches", ROOT / "tmp"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


raw_hashes = {}
for p in RAW.rglob("*"):
    if p.is_file() and p.suffix.lower() in {".pdf", ".doc", ".docx", ".xls", ".xlsx"}:
        raw_hashes.setdefault(sha(p), []).append(p.relative_to(ROOT))

print(f"data/raw 下已有附件 {sum(len(v) for v in raw_hashes.values())} 份 / {len(raw_hashes)} 个不同哈希\n")

missing = []
for d in TEMP_DIRS:
    if not d.exists():
        continue
    for p in d.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".pdf", ".doc", ".docx", ".xls", ".xlsx"}:
            continue
        if p.stat().st_size == 0:
            print(f"空文件（无内容，可删）: {p.relative_to(ROOT)}")
            continue
        h = sha(p)
        rel = p.relative_to(ROOT)
        if h in raw_hashes:
            print(f"已归档  {rel}  ->  {raw_hashes[h][0]}")
        else:
            missing.append(rel)
            print(f"!! 未归档 {rel}  ({p.stat().st_size // 1024} KB)")

print()
if missing:
    print(f"共 {len(missing)} 份原件只在临时目录里，删除前需归档：")
    for m in missing:
        print("  ", m)
else:
    print("临时目录里的原件全部已在 data/raw 归档，可安全删除。")
