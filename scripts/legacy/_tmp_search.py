import sys, urllib.parse, re
from _tmp_probe import get

host = sys.argv[1]
q = sys.argv[2]
siteid = sys.argv[3] if len(sys.argv) > 3 else ""
u = (
    f"http://{host}/jsearchfront/search.do?websiteid={siteid}&q="
    + urllib.parse.quote(q)
    + "&p=1&pos=&cateid=&pg=&searchid=&type=1"
)
try:
    t = get(u)
except Exception as e:
    print("ERR", e)
    raise SystemExit
print("LEN", len(t))
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', t, re.S):
    txt = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    txt = re.sub(r"\s+", " ", txt)
    if txt and len(txt) > 6:
        print(txt[:90], "||", m.group(1)[:110])
