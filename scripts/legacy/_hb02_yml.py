# -*- coding: utf-8 -*-
"""把 playwright 快照 yml 里的 paragraph 文本抽成纯文本。"""
import re, sys

src, dst, url = sys.argv[1], sys.argv[2], sys.argv[3]
t = open(src, encoding="utf-8").read()
lines = []
for m in re.finditer(r"^\s*- (?:paragraph|generic|heading)\s*(?:\[[^\]]*\])?\s*:?\s*(.*)$", t, re.M):
    s = m.group(1).strip()
    s = re.sub(r"^[\"']|[\"']$", "", s)
    if not s or s.startswith("[ref") or s == ":":
        continue
    lines.append(s)
# 去重保序但保留重复段落（招标公告里重复少）
out = []
for l in lines:
    if l in ("相关下载", "相关公告") and len(out) > 20:
        break
    out.append(l)
txt = "\n".join(out)
open(dst, "w", encoding="utf-8").write(url + "\n\n" + txt)
print("chars", len(re.sub(r"\s", "", txt)))
print(txt[:300])
