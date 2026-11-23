# -*- coding: utf-8 -*-
"""核验子智能体产出的每条线索：抓 URL、存快照、校验原句逐字存在、打印上下文。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

ROOT = Path(".")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
FILES = sorted((ROOT / "data/stage/candidates").glob("xy-*.json")) + \
        sorted((ROOT / "data/stage/candidates").glob("jl-c-*.json"))


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·・—\-－]+", "", s or "")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ok, bad = [], []
    for f in FILES:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for i, d in enumerate(data, 1):
            url = (d.get("url") or "").strip()
            quote = (d.get("quote") or "").strip()
            name = (d.get("area_name") or "").strip()
            try:
                r = requests.get(url, headers=UA, timeout=30)
                r.encoding = r.apparent_encoding or "utf-8"
                text = re.sub(r"<[^>]+>", "", r.text)
            except Exception as e:  # noqa: BLE001
                bad.append((f.name, name, "抓取失败", str(e)[:40]))
                continue
            nq, nn = norm(quote), norm(name)
            has_q = nq and nq in norm(text)
            has_n = nn and nn in norm(text)
            status = "OK" if (has_q and has_n) else ("名不符" if not has_n else "原句不符")
            ctx = ""
            if has_n:
                j = norm(text).find(nn)
                ctx = text[max(0, j - 40): j + 80].replace("\n", " ")
            (ok if status == "OK" else bad).append((f.name, name, status, ctx[:120]))
    print(f"通过 {len(ok)}｜不通过 {len(bad)}\n")
    for x in ok:
        print(f"[OK] {x[1]}｜{x[0]}｜{x[3][:80]}")
    print("\n-- 不通过 --")
    for x in bad:
        print(f"[{x[2]}] {x[1]}｜{x[0]}｜{x[3][:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
