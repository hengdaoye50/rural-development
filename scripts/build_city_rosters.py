# -*- coding: utf-8 -*-
"""把 city-extract-{code}.json 转成 ingest_area_roster 的候选表并追加到分省名单文件。

用法：python scripts/build_city_rosters.py 370337 370400 ... （参数是城市码，配置见 CFG）
"""
import csv, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'D:\CODEX\全国乡村片区化数据库')
CAND = ROOT/'data'/'stage'/'candidates'
con = sqlite3.connect(ROOT/'data'/'db'/'片区库.sqlite3')
con.row_factory = sqlite3.Row

# city -> (province_abbr, policy_id, founded_ymd, 只取 note 含关键词的行 or None)
CFG = {
 '370200': ('SD', 'P370337', '2025-06-09', '第二批'),
 '370400': ('SD', 'P370336', '2026-03-11', None),
 '320400': ('JS', 'P320113', '2023-11-24', None),
}
ALIAS = {'西海岸新区': '370211', '常州经开区': '320412', '泰安高新区': '370911'}

counties = {}
for r in con.execute("select region_code,name from region where level='county'"):
    counties.setdefault((r['region_code'][:4], r['name']), r['region_code'])

COLS = ['name','type_code','city_code','county_code','cover_desc','status','founded_ymd',
        'founded_precision','issuer','summary','source_policy_id','rel','parent_area_key']

def load(code):
    p = CAND/f'city-extract-{code}.json'
    return json.loads(p.read_text(encoding='utf-8'))

rows_by_abbr = {}
for code, (abbr, pid, ymd, kw) in CFG.items():
    d = load(code)
    pol = con.execute("select issuer from policy where policy_id=?", (pid,)).fetchone()
    issuer = pol['issuer'] if pol else ''
    rows, miss = [], []
    for a in d['areas']:
        if kw and kw not in (a.get('note') or '') and kw not in (d.get('policy_title') or ''):
            continue
        cn = (a.get('county_name') or '').strip()
        cc = counties.get((code[:4], cn)) or ALIAS.get(cn)
        if not cc:
            miss.append((a['name'], cn)); continue
        rows.append({
            'name': a['name'], 'type_code': 'T01', 'city_code': code, 'county_code': cc,
            'cover_desc': f"{d.get('policy_title','')}：{cn}{('·' + a['town_desc']) if a.get('town_desc') else ''} {a['name']}",
            'status': '运行中', 'founded_ymd': ymd, 'founded_precision': 'day',
            'issuer': issuer,
            'summary': (f"{d.get('policy_title','')}（{ymd}）所列片区。"
                        + (f"乡镇范围：{a['town_desc']}。" if a.get('town_desc') else '')),
            'source_policy_id': pid, 'rel': 'primary',
            'parent_area_key': d.get('policy_title', ''),
        })
    print(f'{code}: 名单 {len(d["areas"])} 条 -> 可入库 {len(rows)}，县区未解析 {miss}')
    rows_by_abbr.setdefault(abbr, []).extend(rows)

for abbr, rows in rows_by_abbr.items():
    p = CAND/f'area-roster-{abbr}.csv'
    old = []
    if p.exists():
        with p.open(encoding='utf-8-sig', newline='') as f:
            rd = csv.DictReader(f); old = list(rd)
    rebuilt_pids = {c[1] for c in CFG.values() if c[0] == abbr}
    old = [r for r in old if r.get('source_policy_id') not in rebuilt_pids]
    have = {(r['name'], r['county_code']) for r in old}
    add = [r for r in rows if (r['name'], r['county_code']) not in have]
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator='\r\n'); w.writeheader()
        for r in old + add:
            w.writerow({c: r.get(c, '') for c in COLS})
    print(f'{abbr}: 原有 {len(old)} + 新增 {len(add)} -> {len(old)+len(add)} 行（{p.name}）')
