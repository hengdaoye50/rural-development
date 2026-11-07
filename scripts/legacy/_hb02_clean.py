# -*- coding: utf-8 -*-
"""清洗 playwright 快照抽取结果中的 ref 残留行。"""
import re, sys

p = sys.argv[1]
url = sys.argv[2]
lines = open(p, encoding="utf-8").read().split("\n")
keep = []
for l in lines:
    if re.match(r"^- (generic|paragraph|text|heading|link|list|listitem|cell|row)\b", l):
        continue
    if "[ref=" in l:
        continue
    keep.append(l.strip().strip('"'))
out = [l for l in keep if l]
txt = "\n".join(out)
if txt.startswith("http"):
    txt = "\n".join(txt.split("\n")[1:]).strip()
open(p, "w", encoding="utf-8").write(url + "\n\n" + txt)
print("chars", len(re.sub(r"\s", "", txt)))
print(txt[:800])
