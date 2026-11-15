"""Append validated policy records to data/stage/batches/POL-SCJS-LINK-policy.jsonl.

Usage: python _tmp_append.py <record.json>
Validates: .gov.cn url, issuer_level enum, areas non-empty, full_text length,
and dedupe against existing urls in the same batch file.
"""
import json, sys, os, re
from pathlib import Path

BATCH = Path('data/stage/batches/POL-SCJS-LINK-policy.jsonl')
ILLEGAL = ('policy_id', 'event_id')
IL = ('province', 'city', 'county', 'town')
SK = ('政策文件', '政府公报', '部门动态', '新闻发布')


def existing_urls():
    s = set()
    if BATCH.exists():
        for ln in BATCH.read_text(encoding='utf-8').splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                d = json.loads(ln)
            except Exception:
                continue
            u = (d.get('url') or '').strip()
            if u:
                s.add(u)
    return s


def main(path):
    rec = json.loads(Path(path).read_text(encoding='utf-8'))
    errs = []
    url = (rec.get('url') or '').strip()
    if not re.match(r'^https?://([\w-]+\.)*gov\.cn(/|$|:)', url):
        errs.append('url 非 .gov.cn: %s' % url)
    if rec.get('issuer_level') not in IL:
        errs.append('issuer_level 非法: %r' % rec.get('issuer_level'))
    if rec.get('source_kind') not in SK:
        errs.append('source_kind 非法: %r' % rec.get('source_kind'))
    if rec.get('credibility') not in ('A', 'B'):
        errs.append('credibility 非法: %r' % rec.get('credibility'))
    areas = rec.get('areas') or []
    if not areas:
        errs.append('areas 为空')
    for a in areas:
        if not a.get('area_id'):
            errs.append('areas 缺 area_id')
        if a.get('rel') not in ('primary', 'support', 'mention'):
            errs.append('rel 非法: %r' % a.get('rel'))
        if a.get('entity_type') not in ('area', 'belt', 'policy'):
            errs.append('entity_type 非法: %r' % a.get('entity_type'))
    ft = (rec.get('full_text') or '').strip()
    if len(ft) < 150:
        errs.append('full_text 过短: %d' % len(ft))
    for k in ILLEGAL:
        if k in rec:
            errs.append('禁止字段 %s' % k)
    if url in existing_urls():
        errs.append('url 已存在（跳过）')
    if errs:
        print('REJECT:')
        for e in errs:
            print('  -', e)
        return 1
    rec['full_text_chars'] = len(re.findall(r'[\u4e00-\u9fff]', ft))
    line = json.dumps(rec, ensure_ascii=False)
    with BATCH.open('a', encoding='utf-8', newline='\n') as f:
        f.write(line + '\n')
    print('APPENDED %s  (%d chars cn)  areas=%s' % (
        rec['title'][:40], rec['full_text_chars'],
        ','.join(a['area_id'] for a in areas)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
