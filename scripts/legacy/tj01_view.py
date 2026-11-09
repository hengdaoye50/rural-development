import io
import re
import sys

path = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
lines = io.open(path, encoding="utf-8").read().split("\n")
print(f"# total lines={len(lines)}")
for i, ln in enumerate(lines[start:start + n], start):
    if re.search(r"HYPERLINK|PAGEREF|TOC \\", ln):
        continue
    print(f"{i}: {ln}")
