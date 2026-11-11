# -*- coding: utf-8 -*-
import json, io, os

P = "data/stage/batches/POL-ZJ06-policy.jsonl"


def append(rec):
    existing = set()
    if os.path.exists(P):
        for line in io.open(P, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            existing.add(o.get("url", ""))
    if rec["url"] in existing:
        print("SKIP dup url:", rec["url"])
        return False
    with io.open(P, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("APPENDED:", rec["title"][:60], "| areas:", len(rec.get("areas", [])))
    return True
