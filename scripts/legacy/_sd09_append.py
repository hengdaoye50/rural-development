import json, sys, os, io

TARGET = os.path.join(os.path.dirname(__file__), "POL-SD09-policy.jsonl")
PART = os.path.join(os.path.dirname(__file__), "_sd09_part.jsonl")

with io.open(PART, encoding="utf-8") as f:
    raw = f.read().strip()

if not raw:
    print("empty part, nothing to do")
    sys.exit(0)

objs = []
for line in raw.splitlines():
    line = line.strip()
    if not line:
        continue
    objs.append(json.loads(line))

existing = set()
if os.path.exists(TARGET):
    with io.open(TARGET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            existing.add(o.get("url", ""))

added = 0
with io.open(TARGET, "a", encoding="utf-8", newline="\n") as f:
    for o in objs:
        if o.get("url") in existing:
            print("SKIP dup url:", o.get("url"))
            continue
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
        existing.add(o.get("url"))
        added += 1
        print("ADDED:", o.get("title")[:60], "| areas=", [a["area_id"] for a in o.get("areas", [])])

with io.open(PART, "w", encoding="utf-8", newline="\n") as f:
    f.write("")

print("total added:", added)
