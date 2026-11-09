import html
import io
import os
import re
import sys
import zipfile

src, dst = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(src)
x = z.read("word/document.xml").decode("utf-8")
x = re.sub(r"</w:p>", "\n", x)
x = re.sub(r"</w:tr>", "\n", x)
x = re.sub(r"</w:tc>", " | ", x)
x = re.sub(r"<w:tab[^>]*/>", "\t", x)
x = re.sub(r"<w:br[^>]*/>", "\n", x)
x = re.sub(r"<[^>]+>", "", x)
x = html.unescape(x)
lines = [re.sub(r"[ \t]+$", "", ln).strip() for ln in x.split("\n")]
out = [ln for ln in lines if ln]
os.makedirs(os.path.dirname(dst), exist_ok=True)
with io.open(dst, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(out) + "\n")
print(f"lines={len(out)} chars={sum(len(l) for l in out)}")
print("\n".join(out[:12]))
