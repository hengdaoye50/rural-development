import sys
from _tmp_probe import get

cands = sys.argv[1:]
for u in cands:
    try:
        t = get(u)
        print("OK", len(t), u)
    except Exception as e:
        print("ERR", u, getattr(e, "code", type(e).__name__))
