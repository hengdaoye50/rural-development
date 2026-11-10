import re, sys
from _tmp_probe import get

t = get(sys.argv[1])
print("LEN", len(t))
# print all art links with text
for m in re.finditer(r'<a[^>]+href="([^"]*art[^"]*)"[^>]*>(.*?)</a>', t, re.S):
    txt = re.sub(r'<[^>]+>', '', m.group(2)).strip()
    if txt:
        print(txt[:80], "||", m.group(1))
