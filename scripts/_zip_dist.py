# -*- coding: utf-8 -*-
"""把 dist/ 打成 Cloudflare Pages 可直接上传的 zip（路径用正斜杠）。"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
root = Path("dist")
out = Path("dist.zip")
out.unlink(missing_ok=True)

n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(root.rglob("*")):
        if p.is_file():
            z.write(p, p.relative_to(root).as_posix())
            n += 1
print(f"{n} files -> {out} ({out.stat().st_size/1024:.0f} KB)")
