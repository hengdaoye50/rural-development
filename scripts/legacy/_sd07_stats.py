import json, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
for f in glob.glob('data/stage/batches/POL-SD0*.jsonl'):
    mx = 0
    n = 0
    for line in open(f, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        n += 1
        mx = max(mx, len(d.get('full_text') or ''))
    print(f, 'records=', n, 'max_full_text=', mx)
