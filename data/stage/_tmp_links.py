import sys, re
import _tmp_fetch as f


def links(url, kw=None, limit=200):
    try:
        h = f.fetch(url)
    except Exception as e:
        print("ERR", url, type(e).__name__, e)
        return []
    out = []
    for m in re.finditer(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h):
        href = m.group(1)
        lab = re.sub(r'(?s)<[^>]+>', '', m.group(2)).strip()
        if kw and kw not in lab:
            continue
        out.append((lab[:60], href))
    for a, b in out[:limit]:
        print(a, "|", b)
    return out


if __name__ == "__main__":
    links(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
