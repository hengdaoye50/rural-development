"""停机前自检：部分批次 JSONL 是否逐行合法（无被截断的末行），并列现存条数。"""
import glob
import json
import os

for p in sorted(glob.glob("data/stage/batches/POL-*.jsonl")):
    bad = 0
    n = 0
    with open(p, "rb") as f:
        raw = f.read()
    if raw and not raw.endswith(b"\n"):
        print(f"!! {os.path.basename(p)} 末行无换行符（可能被截断）")
    for i, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
            n += 1
        except Exception as e:
            bad += 1
            print(f"!! {os.path.basename(p)} 第 {i} 行非法: {e}")
    if "SD1" in p or any(k in p for k in ("HI01", "HA02", "HN02", "HL01", "YN01", "GD04", "HE01")):
        print(f"{os.path.basename(p):<28} {n:>4} 行合法 / {bad} 行坏")
