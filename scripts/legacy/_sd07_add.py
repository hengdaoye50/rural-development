import json, sys, os

OUT = 'data/stage/batches/POL-SD07-policy.jsonl'
DROP = {'begin-->', 'end-->', '打印', '关闭', '关闭窗口', '【打印本页】', '【关闭窗口】',
        '扫一扫在手机打开当前页', '分享到', '微信', '新浪微博', 'QQ空间', '返回顶部'}


def clean_lines(txt):
    out = []
    for l in txt.split('\n'):
        l = l.strip().replace('\ufeff', '')
        if l in DROP:
            continue
        if l.startswith('【') and l.endswith('】'):
            continue
        out.append(l)
    return '\n'.join(out).strip()


def main():
    meta_path, text_path = sys.argv[1], sys.argv[2]
    rec = json.load(open(meta_path, encoding='utf-8'))
    ft = clean_lines(open(text_path, encoding='utf-8').read())
    if len(ft) < 300:
        print('REFUSED: full_text too short (%d chars)' % len(ft))
        sys.exit(2)
    rec['full_text'] = ft
    rec['full_text_chars'] = len([c for c in ft if not c.isspace()])
    order = ['title', 'doc_no', 'issuer', 'issuer_level', 'issued_ymd', 'published_ymd', 'doc_type',
             'source_kind', 'province_code', 'city_code', 'county_code', 'instruments', 'scope_desc',
             'target_areas', 'budget_wan', 'valid_state', 'url', 'credibility', 'summary', 'slug',
             'fetched_at', 'full_text_chars', 'full_text', 'areas', 'events']
    out = {k: rec[k] for k in order if k in rec}
    for k in rec:
        if k not in out:
            out[k] = rec[k]
    line = json.dumps(out, ensure_ascii=False)
    n0 = sum(1 for _ in open(OUT, encoding='utf-8')) if os.path.exists(OUT) else 0
    with open(OUT, 'a', encoding='utf-8', newline='\n') as f:
        f.write(line + '\n')
        f.flush()
    print('OK appended: %s | chars=%d | records=%d' % (out['title'][:40], out['full_text_chars'], n0 + 1))


if __name__ == '__main__':
    main()
