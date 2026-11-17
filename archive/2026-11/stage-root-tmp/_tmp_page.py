import re, sys
import _tmp_fetch as f

url = sys.argv[1]
kw = sys.argv[2] if len(sys.argv) > 2 else "工作报告"
h = f.fetch(url)
# pagination hints
for m in re.finditer(r'(?i)(page=\d+|createPageHTML\([^)]*\)|totalpage[^,;]*)', h):
    print("PAGE:", m.group(0)[:120])
print("---")
seen = set()
for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
    lab = re.sub(r'\s+', ' ', re.sub(r'(?s)<[^>]+>', '', m.group(2))).strip()
    if kw and kw not in lab:
        continue
    if lab in seen:
        continue
    seen.add(lab)
    print(lab[:50], "|", m.group(1)[:90])
