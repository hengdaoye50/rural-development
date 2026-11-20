# -*- coding: utf-8 -*-
"""apply_city_roster_scan：已 matched 的行保持 matched（只补 note），其余按扫描判定。"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
p = Path(r'D:\CODEX\全国乡村片区化数据库\scripts\apply_city_roster_scan.py')
t = p.read_text(encoding='utf-8')
old = '''        cur_in_db = int((r.get("in_db_count") or "0") or 0)
        if st == "matched" and cur_in_db == 0:
            st = "partial"  # 名单找到但条目还没入库：只能算待入库'''
new = '''        cur_in_db = int((r.get("in_db_count") or "0") or 0)
        if r.get("status") == "matched" and cur_in_db > 0:
            st = "matched"  # 已对账的不因扫描结论降级
        elif st == "matched" and cur_in_db == 0:
            st = "partial"  # 名单找到但条目还没入库：只能算待入库'''
assert old in t
t = t.replace(old, new)
# tail 里补 URL，便于回溯
t = t.replace('''        if excerpt:
            tail += f" 原文：{excerpt[:120]}"''',
'''        tail += f" 来源：{url}"
        if excerpt:
            tail += f"｜原文：{excerpt[:100]}"''')
p.write_text(t, encoding='utf-8')
print('ok')
