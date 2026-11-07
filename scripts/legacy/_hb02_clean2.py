# -*- coding: utf-8 -*-
"""清洗 playwright 快照抽取结果：保留段落文本，去掉 ref 前缀。"""
import re, sys

p = sys.argv[1]
url = sys.argv[2]
lines = open(p, encoding="utf-8").read().split("\n")
keep = []
for l in lines:
    s = l.strip()
    m = re.match(r"- (?:paragraph|text|heading|generic)(?: \[[^\]]*\])?(?: \"[^\"]*\")?\s*:\s*(.*)$", s)
    if m:
        v = m.group(1).strip().strip('"')
        if v:
            keep.append(v)
        continue
    if re.match(r"- (link|list|listitem|cell|row|table|rowgroup|navigation|status|contentinfo)\b", s):
        continue
    if not s or "[ref=" in s:
        continue
    keep.append(s.strip('"'))
txt = "\n".join(keep).strip()
if txt.startswith("http"):
    txt = "\n".join(txt.split("\n")[1:]).strip()
open(p, "w", encoding="utf-8").write(url + "\n\n" + txt)
print("chars", len(re.sub(r"\s", "", txt)))
print(txt[:1500])
