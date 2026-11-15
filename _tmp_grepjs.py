import re
t = open('_tmp_js3.html', encoding='utf-8', errors='replace').read()
for m in sorted(set(re.findall(r'[\w/\.\-]*interfaces[\w/\.\-]*', t))):
    print('IFACE:', m)
for m in sorted(set(re.findall(r'url\s*:\s*[\'"]([^\'"]+)[\'"]', t))):
    print('URL:', m)
for m in sorted(set(re.findall(r'[\'"]([^\'"]*jsearchfront[^\'"]*)[\'"]', t))):
    print('JS:', m)
for m in sorted(set(re.findall(r'<script[^>]*src=[\'"]([^\'"]+)[\'"]', t))):
    print('SRC:', m)
