import sys, re, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
url = sys.argv[1]
h = t.fetch(url)
pats = sys.argv[2:] or ["search", "so.", "jpaas", "ajax", "json", ".do"]
seen = set()
for p in pats:
    for m in re.finditer(r"(?i)[\"']([^\"']*" + re.escape(p) + r"[^\"']{0,100})[\"']", h):
        v = m.group(1)
        if len(v) < 6 or v in seen:
            continue
        seen.add(v)
        print(v)
