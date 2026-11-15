"""Build a record JSON from a spec file.

Spec: JSON with "meta": {...}, and optionally
  "body_file": path to extracted text, "start": marker, "end": marker
  or "body": literal text.
Writes out to spec["out"].
"""
import json, sys
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
meta = spec['meta']
if 'body_file' in spec:
    t = Path(spec['body_file']).read_text(encoding='utf-8')
    if spec.get('start'):
        i = t.find(spec['start'])
        assert i >= 0, 'start marker not found'
        t = t[i:]
    if spec.get('end'):
        j = t.find(spec['end'])
        assert j >= 0, 'end marker not found'
        t = t[:j + len(spec['end'])]
    body = t.strip()
else:
    body = spec['body'].strip()

rec = dict(meta)
rec['full_text'] = body
out = Path(spec['out'])
out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
print('WROTE', out, 'body_len', len(body))
