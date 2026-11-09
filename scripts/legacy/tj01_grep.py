import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_probe import fetch  # noqa: E402


def text_of(html):
    b = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    b = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</td>|</tr>|</h\d>", "\n", b)
    b = re.sub(r"(?s)<[^>]+>", "", b)
    import html as h

    b = h.unescape(b)
    b = re.sub(r"[ \t\u3000]+", " ", b)
    b = re.sub(r"\n\s*\n+", "\n", b)
    return b.strip()


if __name__ == "__main__":
    url = sys.argv[1]
    kws = sys.argv[2].split(",")
    win = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 120
    body = text_of(fetch(url))
    print(f"# {url} chars={len(body)}")
    for kw in kws:
        for m in re.finditer(kw, body):
            s = max(0, m.start() - win)
            print(f"[{kw}] ...{body[s:m.end() + win].replace(chr(10), ' ')}...")
