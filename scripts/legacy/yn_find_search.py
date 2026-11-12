# -*- coding: utf-8 -*-
"""一次性探针：从指定页面找站内搜索表单，并试打搜索接口。"""
from __future__ import annotations

import re
import sys
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings()
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

url = sys.argv[1]
r = requests.get(url, headers=H, timeout=30, verify=False)
r.encoding = "utf-8"
s = BeautifulSoup(r.text, "html.parser")
for f in s.find_all("form"):
    print("FORM action=", f.get("action"), "method=", f.get("method"))
    for i in f.find_all(["input", "select"]):
        print("   ", i.get("name"), i.get("id"), i.get("type"))
for a in s.find_all("a"):
    h = a.get("href") or ""
    if re.search(r"search|sousuo|so\.", h, re.I):
        print("SEARCHLINK", a.get_text(strip=True), h)
