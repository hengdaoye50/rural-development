import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

BATCH = "data/stage/batches/POL-ZJ03-policy.jsonl"
raw = io.open(BATCH, "rb").read()
lines = raw.decode("utf-8").splitlines()
targets = {}
for i, line in enumerate(lines):
    if not line.strip():
        continue
    o = json.loads(line)
    if o["slug"] in {"zj-wz-py-fazhanzhou-guihua-gongshigao", "zj-wz-wc-fazhanzhou-guihua-gongshi-tuban"}:
        nw = len(re.sub(r"\s", "", o["full_text"]))
        if o["full_text_chars"] != nw:
            o["full_text_chars"] = nw
            targets[i] = json.dumps(o, ensure_ascii=False)
if not targets:
    print("nothing to fix")
    raise SystemExit
if io.open(BATCH, "rb").read() != raw:
    print("ABORT: file changed concurrently")
    raise SystemExit
new = list(lines)
for i, line in targets.items():
    new[i] = line
io.open(BATCH, "w", encoding="utf-8", newline="\n").write("\n".join(new) + "\n")
print("fixed lines", sorted(k + 1 for k in targets))
print("total", len(new))
