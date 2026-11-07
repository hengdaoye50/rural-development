"""批量入库：把 data/stage/POL-*.jsonl 全部按批次串行入库。

并行采集的收尾命令。去重由 ingest_policy 内部完成（url / doc_no+issuer），
所以重复执行安全；已入库过的批次再跑只会全部跳过。

用法：
  python scripts/ingest_all.py --dry-run          # 只解析，不写盘
  python scripts/ingest_all.py                  # 入库所有批次
  python scripts/ingest_all.py ZJ01 SD01        # 只入库匹配的分片
  python scripts/ingest_all.py --then-pipeline   # 入库后接着 merge/build/validate
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "stage"
sys.path.insert(0, str(ROOT / "scripts"))

from ingest_policy import ingest  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    pipeline = "--then-pipeline" in args
    filters = [a for a in args if not a.startswith("--")]

    files = sorted((STAGE / "batches").glob("POL-*.jsonl"))
    if filters:
        files = [f for f in files if any(k.lower() in f.name.lower() for k in filters)]
    if not files:
        print("没有找到 data/stage/batches/POL-*.jsonl")
        return 1

    total_p = total_m = total_e = 0
    for f in files:
        naming = f.stem
        print(f"\n{'='*70}\n[{naming}]  {f.name}  ({f.stat().st_size // 1024} KB)")
        rc = ingest(f, dry_run=dry)
        if rc != 0:
            print(f"  !! 入库失败，跳过后续：{naming}")
            return rc
    print(f"\n{'='*70}\n批次处理完成：{len(files)} 个文件")

    if pipeline and not dry:
        for cmd in ("merge_by_province.py", "build_db.py", "validate_db.py"):
            print(f"\n--- {cmd} ---")
            subprocess.run([sys.executable, str(ROOT / "scripts" / cmd)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
