# -*- coding: utf-8 -*-
"""下载 PDF 并抽取文本（需 pypdf）。"""
import os, sys, urllib.request

HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
      "Accept-Encoding": "identity", "Connection": "close"}
OUT = os.path.join("scripts", "legacy", "_hb02_out")
os.makedirs(OUT, exist_ok=True)

url = sys.argv[1]
key = sys.argv[2]
pdf = os.path.join(OUT, key + ".pdf")
data = urllib.request.urlopen(urllib.request.Request(url, headers=HD), timeout=120).read()
open(pdf, "wb").write(data)
print("bytes", len(data))
try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader
rd = PdfReader(pdf)
print("pages", len(rd.pages))
txt = []
for p in rd.pages:
    try:
        txt.append(p.extract_text() or "")
    except Exception as e:
        txt.append("")
t = "\n".join(txt)
open(os.path.join(OUT, key + ".md"), "w", encoding="utf-8").write(url + "\n\n" + t)
print("chars", len(t))
print(t[:600])
