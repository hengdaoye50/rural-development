# -*- coding: utf-8 -*-
"""从 workflow 输出里抽出 cities JSON 存盘。"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
SRC = Path(r'C:\Users\zjh22\AppData\Local\Temp\dsh-spill-v8fbO6\session-e7124277a637\e59bcf27dfff-job_output.txt')
t = SRC.read_text(encoding='utf-8', errors='replace')
i = t.index('{')
# cities 数组结束于  '  ],\n  "specials": ['
j = t.index('"specials"')
head = t[i:j]
head = head.rstrip().rstrip(',')
if not head.rstrip().endswith(']'):
    head = head.rstrip() + ']}'
else:
    head = head.rstrip() + '}'
data = json.loads(head)
cities = data['cities']
print('cities', len(cities))
from collections import Counter
print(Counter(c['status_suggestion'] for c in cities))
print('found', sum(1 for c in cities if c['found']))
OUT = Path(r'D:\CODEX\全国乡村片区化数据库\data\stage\candidates\city-roster-scan-2026-11-21.json')
OUT.write_text(json.dumps({'cities': cities}, ensure_ascii=False, indent=1), encoding='utf-8')
print('wrote', OUT)
for c in cities:
    if c['status_suggestion'] in ('matched', 'partial'):
        print(f"  {c['city_code']} {c['city_name']} {c['status_suggestion']} 数={c['count_int']} 名单={c['names_listed']} {c['roster_name'][:30]}")
