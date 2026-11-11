import re, sys, html
from _tmp_probe import get

u = sys.argv[1]
t = get(u)
# strip scripts/styles
t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S | re.I)
m = re.search(r'<div[^>]*(id="zoom"|class="[^"]*(article|content|zoom|TRS_Editor)[^"]*")[^>]*>(.*?)</div>\s*(?:</div>)?', t, re.S | re.I)
body = m.group(3) if m else t
body = re.sub(r"<\s*br\s*/?>", "\n", body, flags=re.I)
body = re.sub(r"</\s*(p|div|li|tr|h\d)\s*>", "\n", body, flags=re.I)
body = re.sub(r"</\s*(td|th)\s*>", " | ", body, flags=re.I)
body = re.sub(r"<[^>]+>", "", body)
body = html.unescape(body)
body = re.sub(r"[ \t\u3000]+", " ", body)
body = re.sub(r"\n\s*\n+", "\n\n", body)
print("URL:", u)
print("LEN:", len(body))
print(body.strip()[:8000])
