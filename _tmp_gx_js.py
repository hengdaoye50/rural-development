import io
from _tmp_gx_probe import get
s, b = get('http://www.gxzf.gov.cn/material/wybsearch/js/wyb_search.js')
open('_tmp_wyb_search.js', 'wb').write(b)
print(s, len(b))
print(b.decode('utf-8', errors='replace')[:3000])
