# -*- coding: utf-8 -*-
"""生成自包含的省级分级设色单页：`data/export/map/preview.html`。

数据来自 `data/export/map/provinces.geojson`（先跑 `export_map_data.py`）。
无外部依赖、无网络请求，双击即可看：指标切换、悬停提示、点击看省详情。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "export" / "map" / "provinces.geojson"
OUT = ROOT / "data" / "export" / "map" / "preview.html"

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>全国乡村片区化数据库 · 省级分布</title>
<style>
:root{--ink:#1b2430;--ink2:#4a5665;--ink3:#7b8794;--line:#e3e8ee;--bg:#f7f9fa;--accent:#0f6f6c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.6 "PingFang SC","Microsoft YaHei",system-ui,sans-serif}
header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;
  padding:14px 22px;background:#fff;border-bottom:1px solid var(--line)}
h1{font-size:17px;margin:0}
.sub{font-size:12px;color:var(--ink3)}
.seg{display:flex;gap:4px;background:#eef1f4;padding:3px;border-radius:999px}
.seg button{border:0;background:transparent;padding:5px 12px;border-radius:999px;cursor:pointer;
  font-size:13px;color:var(--ink2)}
.seg button.on{background:#fff;color:var(--accent);font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,.08)}
main{display:grid;grid-template-columns:1fr 300px;gap:16px;padding:16px 22px 8px;max-width:1400px;margin:0 auto}
@media (max-width:900px){main{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}
svg{width:100%;height:auto;display:block}
path.prov{stroke:#fff;stroke-width:.6;cursor:pointer;transition:opacity .15s}
path.prov:hover{opacity:.82}
path.prov.sel{stroke:var(--accent);stroke-width:2}
#tip{position:fixed;pointer-events:none;background:rgba(20,30,40,.92);color:#fff;font-size:12px;
  padding:6px 9px;border-radius:6px;display:none;z-index:99;white-space:nowrap}
.legend{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink2);margin-top:8px;flex-wrap:wrap}
.sw{width:26px;height:10px;border-radius:2px}
.panel h2{font-size:16px;margin:2px 0 10px}
.kv{display:grid;grid-template-columns:1fr auto;gap:6px 10px;font-size:13px;padding:6px 0;border-bottom:1px dashed var(--line)}
.kv b{font-weight:600}
.note{font-size:12px;color:var(--ink3);padding:0 22px 22px;max-width:1400px;margin:0 auto;line-height:1.7}
.empty{color:var(--ink3);font-size:13px}
</style>
</head>
<body>
<header>
  <div>
    <h1>全国乡村片区化数据库 · 省级分布</h1>
    <div class="sub">快照 __SNAPSHOT__｜在册 __ACTIVE__ 条｜县覆盖 __COUNTY__/2856</div>
  </div>
  <div class="seg" id="seg">
    <button data-m="areas" class="on">片区数</button>
    <button data-m="main">主统计</button>
    <button data-m="wide">宽统计</button>
    <button data-m="pending_share">待核占比</button>
  </div>
</header>
<main>
  <div class="card">
    <svg id="map" viewBox="0 0 1000 760" role="img" aria-label="省级分布"></svg>
    <div class="legend" id="legend"></div>
  </div>
  <div class="card panel" id="panel">
    <h2 id="p-name">点省份看详情</h2>
    <div id="p-body" class="empty">全国 31 个省级单位（港澳台不纳入）。<br><br>指标可切换；颜色越深数值越高。<br>灰色表示库内暂无记录，不等于当地没有片区。</div>
  </div>
</main>
<p class="note">口径：片区数为在册 active（含待核）；主统计＝2022 年后成立且有 primary/support 依据（A+B）；
宽统计＝主统计＋时间不详（A+B+C）；待核占比＝待核 / 在册。<br>
0 值／灰色只代表库里没有收录（县覆盖 615/2856），对外引用必须同时标注覆盖率。</p>
<div id="tip"></div>
<script>
const DATA = __JSON__;
const META = __META__;
const svg = document.getElementById('map');
const tip = document.getElementById('tip');
const W = 1000, H = 760;
let metric = 'areas';
let selected = null;

function merc(lon, lat){
  const x = lon * Math.PI / 180;
  const y = Math.log(Math.tan(Math.PI/4 + (lat*Math.PI/180)/2));
  return [x, y];
}
const feats = DATA.features.filter(f => f.geometry);
const all = [];
feats.forEach(f => {
  const g = f.geometry;
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
  polys.forEach(p => p.forEach(ring => ring.forEach(c => all.push(c))));
});
let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
all.forEach(c => {
  const [x, y] = merc(c[0], c[1]);
  minX = Math.min(minX, x); maxX = Math.max(maxX, x);
  minY = Math.min(minY, y); maxY = Math.max(maxY, y);
});
const pad = 24;
const sx = (W - pad*2) / (maxX - minX);
const sy = (H - pad*2) / (maxY - minY);
const s = Math.min(sx, sy);
const ox = pad + ((W - pad*2) - (maxX - minX)*s)/2;
const oy = pad + ((H - pad*2) - (maxY - minY)*s)/2;
function proj(lon, lat){ const [x, y] = merc(lon, lat); return [ox + (x-minX)*s, oy + (maxY-y)*s]; }
function pathOf(f){
  const g = f.geometry;
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
  return polys.map(p => p.map(ring => ring.map((c,i) => {
    const [x, y] = proj(c[0], c[1]);
    return (i ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
  }).join('') + 'Z').join('')).join(' ');
}
const COLORS = ['#eef3f2','#cfe3e0','#9dc9c4','#5fa8a1','#2b7f78','#0f6f6c'];
const WARM = ['#f7f2ea','#f3e2c8','#e9c79a','#dd9f62','#c9743a','#a2452a'];
function bucket(v, max){
  if (!v) return 0;
  const r = v / max;
  if (r > .66) return 5; if (r > .4) return 4; if (r > .2) return 3; if (r > .08) return 2; return 1;
}
function vals(){ return DATA.features.map(f => f.properties[metric] || 0); }
let maxV = Math.max(...vals());
let maxP = Math.max(...DATA.features.map(f => f.properties.pending_share || 0));
function colorOf(p){
  if (metric === 'pending_share'){
    if (!p.areas) return '#f2f4f5';
    return WARM[bucket(p.pending_share, maxP)];
  }
  if (!p.areas) return '#f2f4f5';
  return COLORS[bucket(p[metric], maxV)];
}
function draw(){
  maxV = Math.max(...vals());
  svg.innerHTML = '';
  DATA.features.forEach((f, i) => {
    if (!f.geometry) return;
    const el = document.createElementNS('http://www.w3.org/2000/svg','path');
    el.setAttribute('d', pathOf(f));
    el.setAttribute('class', 'prov' + (selected === i ? ' sel' : ''));
    el.setAttribute('fill', colorOf(f.properties));
    el.dataset.i = i;
    el.addEventListener('mousemove', e => {
      const p = f.properties;
      tip.style.display = 'block';
      tip.style.left = (e.clientX + 14) + 'px';
      tip.style.top = (e.clientY + 12) + 'px';
      tip.innerHTML = p.name + '｜片区 ' + (p.areas||0) + '｜主 ' + (p.main||0) +
        '｜待核 ' + (p.pending||0) + ' (' + (p.pending_share||0) + '%)';
    });
    el.addEventListener('mouseleave', () => tip.style.display = 'none');
    el.addEventListener('click', () => { selected = i; draw(); show(f.properties); });
    svg.appendChild(el);
  });
  drawLegend();
}
function drawLegend(){
  const box = document.getElementById('legend');
  if (metric === 'pending_share'){
    box.innerHTML = '<span>待核占比</span>' + WARM.map((c,i) =>
      '<span class="sw" style="background:'+c+'"></span>').join('') +
      '<span>0 → 100%</span><span style="margin-left:14px">灰＝无记录</span>';
    return;
  }
  const label = {areas:'片区数', main:'主统计', wide:'宽统计'}[metric];
  box.innerHTML = '<span>'+label+'</span>' + COLORS.map((c,i) =>
    '<span class="sw" style="background:'+c+'"></span>').join('') +
    '<span>0 → '+maxV+'</span><span style="margin-left:14px">灰＝无记录</span>';
}
function show(p){
  const rows = [
    ['片区数（在册）', p.areas||0],
    ['主统计 A+B', p.main||0],
    ['宽统计 A+B+C', p.wide||0],
    ['待核', p.pending||0],
    ['待核占比', (p.pending_share||0) + '%'],
    ['有 primary/support', p.strong||0],
    ['覆盖县', p.counties||0],
    ['象征单元 belt', p.belt||0],
    ['政策文件', p.policy||0],
  ];
  document.getElementById('p-name').textContent = p.name + '（' + p.code + '）';
  document.getElementById('p-body').className = '';
  document.getElementById('p-body').innerHTML = rows.map(r =>
    '<div class="kv"><span>'+r[0]+'</span><b>'+r[1]+'</b></div>').join('');
}
document.getElementById('seg').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  metric = b.dataset.m;
  [...document.querySelectorAll('#seg button')].forEach(x => x.classList.toggle('on', x === b));
  draw();
});
draw();
</script>
</body>
</html>
"""


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not SRC.exists():
        print("缺 provinces.geojson，先跑 scripts/export_map_data.py")
        return 1
    gj = json.loads(SRC.read_text(encoding="utf-8"))
    feats = gj["features"]
    props = [f["properties"] for f in feats]
    active = sum(p.get("areas", 0) for p in props)
    county = sum(p.get("counties", 0) for p in props)
    meta = {
        "snapshot": "2026-11-21",
        "active": active,
        "county": county,
    }
    html = (TPL
            .replace("__JSON__", json.dumps(gj, ensure_ascii=False))
            .replace("__META__", json.dumps(meta, ensure_ascii=False))
            .replace("__SNAPSHOT__", meta["snapshot"])
            .replace("__ACTIVE__", f"{active:,}")
            .replace("__COUNTY__", str(county)))
    OUT.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT.relative_to(ROOT)}（{OUT.stat().st_size/1024:.0f}KB，{len(feats)} 要素）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
