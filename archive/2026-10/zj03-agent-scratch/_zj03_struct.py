import sys, re, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("t", r"D:\CODEX\全国乡村片区化数据库\data\stage\_zj03_tool.py")
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
h = t.fetch(sys.argv[1])
for m in re.finditer(r'(?is)<(div|td|article|section)[^>]*(id|class)="([^"]{0,120})"[^>]*>', h):
    print(m.group(1), "|", m.group(3))
