import sys, re, os
import _tmp_fetch as f

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gzbg")
os.makedirs(OUT, exist_ok=True)


def save(tag, url):
    h = f.fetch(url)
    t = f.text_of(h)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    p = os.path.join(OUT, tag + ".txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("URL: " + url + "\n")
        fh.write(t)
    hits = [m.start() for m in re.finditer("片区", t)]
    print(tag, "chars=", len(t), "片区count=", len(hits), "->", p)
    return t


if __name__ == "__main__":
    save(sys.argv[1], sys.argv[2])
