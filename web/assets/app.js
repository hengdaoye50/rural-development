/* 全国乡村片区化数据库 · 共享脚本（经典脚本，无依赖） */
(function () {
  "use strict";
  var RD = window.RD || {};
  var GEO = window.RD_GEO || null;
  var fmt = function (n) { return (n == null ? "—" : Number(n).toLocaleString("zh-CN")); };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- 导航高亮 ---------- */
  function markNav() {
    var path = (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "");
    $$("nav.main a").forEach(function (a) {
      var href = (a.getAttribute("href") || "").replace(/\.html$/, "");
      if (href === path || (path === "index" && href === "index")) a.classList.add("on");
    });
  }

  /* ---------- 地图 ---------- */
  var PALETTE_DARK = ["#4E2140", "#6B2A56", "#8E376E", "#B24A88", "#D06DA6", "#E99CC6"];
  var PALETTE_LIGHT = ["#EDE2EA", "#DCC0D6", "#C99CC2", "#B172AC", "#94468F", "#7E0C6E"];
  var palette = PALETTE_LIGHT;

  /** 从 CSS 变量读调色板：主题由 CSS 决定，JS 不再自己判断深/浅，避免两者打架 */
  function syncPalette() {
    try {
      var cs = window.getComputedStyle(document.documentElement);
      var out = [];
      for (var i = 0; i < 6; i++) {
        var v = cs.getPropertyValue("--map-" + i).trim();
        out.push(v || (prefersDark() ? PALETTE_DARK[i] : PALETTE_LIGHT[i]));
      }
      palette = out;
    } catch (e) {
      palette = prefersDark() ? PALETTE_DARK : PALETTE_LIGHT;
    }
  }
  function prefersDark() {
    try { return window.matchMedia("(prefers-color-scheme: dark)").matches; }
    catch (e) { return false; }
  }
  syncPalette();

  function merc(lon, lat) {
    return [lon * Math.PI / 180, Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360))];
  }

  function buildMap(el, opts) {
    if (!GEO || !GEO.features) return null;
    var cs = window.getComputedStyle(el);
    var W = 760, H = 460, s = 1, ox = 0, oy = 0, minX = 0, maxX = 1, minY = 0, maxY = 1;
    var pad = 10;
    var feats = GEO.features.filter(function (f) { return f.geometry; });
    var pts = [];
    feats.forEach(function (f) {
      var g = f.geometry;
      var polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      polys.forEach(function (p) {
        p.forEach(function (ring) { ring.forEach(function (c) { pts.push(c); }); });
      });
    });
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    pts.forEach(function (c) {
      var p = merc(c[0], c[1]);
      if (p[0] < minX) minX = p[0];
      if (p[0] > maxX) maxX = p[0];
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    });
    var s = Math.min((W - pad * 2) / (maxX - minX), (H - pad * 2) / (maxY - minY));
    var ox = pad + ((W - pad * 2) - (maxX - minX) * s) / 2;
    var oy = pad + ((H - pad * 2) - (maxY - minY) * s) / 2;

    function layout() {
      W = Math.max(320, Math.round(el.clientWidth - parseFloat(cs.paddingLeft || 0) - parseFloat(cs.paddingRight || 0)));
      H = Math.max(280, Math.round(el.clientHeight - parseFloat(cs.paddingTop || 0) - parseFloat(cs.paddingBottom || 0)));
      s = Math.min((W - pad * 2) / (maxX - minX), (H - pad * 2) / (maxY - minY));
      ox = pad + ((W - pad * 2) - (maxX - minX) * s) / 2;
      oy = pad + ((H - pad * 2) - (maxY - minY) * s) / 2;
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    }
    function proj(lon, lat) {
      var p = merc(lon, lat);
      return [ox + (p[0] - minX) * s, oy + (maxY - p[1]) * s];
    }
    function pathOf(f) {
      var g = f.geometry;
      var polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      return polys.map(function (p) {
        return p.map(function (ring) {
          return ring.map(function (c, i) {
            var q = proj(c[0], c[1]);
            return (i ? "L" : "M") + q[0].toFixed(1) + " " + q[1].toFixed(1);
          }).join("") + "Z";
        }).join("");
      }).join(" ");
    }

    var metric = (opts && opts.metric) || "areas";
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "map");
    svg.setAttribute("role", "img");
    var tip = document.createElement("div");
    tip.className = "maptip";
    el.appendChild(svg);
    el.appendChild(tip);
    layout();
    window.addEventListener("resize", function () {
      clearTimeout(el.__rdT);
      el.__rdT = setTimeout(function () { layout(); draw(); }, 120);
    });
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
        syncPalette();
        draw();
        if (opts && opts.onRedraw) opts.onRedraw();
      });
    } catch (e) { /* 旧浏览器忽略 */ }

    function maxOf(m) {
      return Math.max.apply(null, feats.map(function (f) { return f.properties[m] || 0; }));
    }
    function bucket(v, max) {
      if (!v) return 0;
      var r = v / max;
      if (r > 0.66) return 5;
      if (r > 0.4) return 4;
      if (r > 0.2) return 3;
      if (r > 0.08) return 2;
      return 1;
    }
    var maxV = maxOf(metric);

    function draw() {
      maxV = maxOf(metric);
      svg.innerHTML = "";
      feats.forEach(function (f) {
        var p = document.createElementNS("http://www.w3.org/2000/svg", "path");
        p.setAttribute("d", pathOf(f));
        p.setAttribute("class", "p");
        p.setAttribute("fill", palette[bucket(f.properties[metric] || 0, maxV)]);
        p.addEventListener("mousemove", function (e) {
          var pr = f.properties;
          var rect = el.getBoundingClientRect();
          tip.style.display = "block";
          tip.style.left = (e.clientX - rect.left + 14) + "px";
          tip.style.top = (e.clientY - rect.top + 12) + "px";
          tip.innerHTML = (pr.name || pr.code) + "｜片区 " + fmt(pr.areas) +
            "｜主 " + fmt(pr.main) + "｜待核 " + fmt(pr.pending) + "（" + (pr.pending_share || 0) + "%）";
        });
        p.addEventListener("mouseleave", function () { tip.style.display = "none"; });
        p.addEventListener("click", function () {
          if (opts && opts.onSelect) opts.onSelect(f.properties);
          else location.href = "map.html?prov=" + f.properties.code;
        });
        svg.appendChild(p);
      });
      if (opts && opts.onRedraw) opts.onRedraw();
    }

    return {
      el: el,
      setMetric: function (m) { metric = m; draw(); },
      maxOf: maxOf,
      getPalette: function () { return palette; }
    };
  }

  /* ---------- 排行榜 ---------- */
  function renderRank(el, metric, rows) {
    var list = rows.slice().sort(function (a, b) { return (b[metric] || 0) - (a[metric] || 0); }).slice(0, 6);
    el.innerHTML = list.map(function (p, i) {
      return '<li data-code="' + p.code + '"><span class="i">' + (i + 1) + "</span>" +
        "<span>" + p.name + "</span><span class=\"v\">" + fmt(p[metric]) +
        (metric === "pending_share" ? "%" : "") + "</span></li>";
    }).join("");
    $$("li", el).forEach(function (li) {
      li.addEventListener("click", function () { location.href = "map.html?prov=" + li.getAttribute("data-code"); });
    });
  }

  /* ---------- 条形图 ---------- */
  function renderBars(el, rows) {
    var max = Math.max.apply(null, rows.map(function (r) { return r.v; }));
    el.innerHTML = rows.map(function (r) {
      return '<div class="bar"><span>' + r.label + '</span><span class="track">' +
        '<span class="fill' + (r.gold ? " gold" : "") + '" style="width:' +
        (max ? (r.v / max) * 100 : 0).toFixed(1) + '%"></span></span>' +
        '<span class="v">' + fmt(r.v) + "</span></div>";
    }).join("");
  }

  /* ---------- 导出 ---------- */
  window.RDKit = { fmt: fmt, buildMap: buildMap, renderRank: renderRank, renderBars: renderBars };

  document.addEventListener("DOMContentLoaded", markNav);
})();
