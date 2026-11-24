/* 全国乡村片区化数据库 · 共享脚本（经典脚本，无依赖） */
(function () {
  "use strict";
  var RD = window.RD || {};
  var GEO = window.RD_GEO || null;
  var fmt = function (n) { return (n == null ? "—" : Number(n).toLocaleString("zh-CN")); };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  /** 文本转义：所有拼接进 innerHTML 的名字都过一遍 */
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };

  /* ---------- 导航高亮 ---------- */
  function markNav() {
    var path = (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "");
    $$("nav.main a").forEach(function (a) {
      var href = (a.getAttribute("href") || "").replace(/\.html$/, "");
      if (href === path || (path === "index" && href === "index")) a.classList.add("on");
    });
  }

  /* ---------- 移动端导航（≤640px 时出现「菜单」按钮） ---------- */
  function mobileNav() {
    var nav = $("nav.main");
    if (!nav || $(".navtoggle")) return;
    var btn = document.createElement("button");
    btn.className = "navtoggle";
    btn.type = "button";
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "primary-nav");
    btn.textContent = "菜单";
    nav.id = nav.id || "primary-nav";
    nav.parentNode.insertBefore(btn, nav);
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- 地图 ---------- */
  var PALETTE_DARK = ["#4E2140", "#6B2A56", "#8E376E", "#B24A88", "#D06DA6", "#E99CC6"];
  var PALETTE_LIGHT = ["#EDE2EA", "#DCC0D6", "#C99CC2", "#B172AC", "#94468F", "#7E0C6E"];
  var palette = PALETTE_LIGHT;
  var NA_CODES = { "710000": 1, "810000": 1, "820000": 1 }; // 台港澳：资料暂缺，不参与着色
  var JD_CODE = "100000_JD";

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
  function bboxOf(feats) {
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    feats.forEach(function (f) {
      var g = f.geometry;
      var polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      polys.forEach(function (p) {
        p.forEach(function (ring) {
          ring.forEach(function (c) {
            var q = merc(c[0], c[1]);
            if (q[0] < minX) minX = q[0];
            if (q[0] > maxX) maxX = q[0];
            if (q[1] < minY) minY = q[1];
            if (q[1] > maxY) maxY = q[1];
          });
        });
      });
    });
    return { minX: minX, maxX: maxX, minY: minY, maxY: maxY };
  }
  function pathBuilder(feature, minX, maxY, s, ox, oy) {
    var g = feature.geometry;
    var polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
    return polys.map(function (p) {
      return p.map(function (ring) {
        return ring.map(function (c, i) {
          var q = merc(c[0], c[1]);
          return (i ? "L" : "M") + (ox + (q[0] - minX) * s).toFixed(1) + " " +
            (oy + (maxY - q[1]) * s).toFixed(1);
        }).join("") + "Z";
      }).join("");
    }).join(" ");
  }

  function buildMap(el, opts) {
    if (!GEO || !GEO.features) return null;
    var all = GEO.features.filter(function (f) { return f.geometry; });
    var jd = all.filter(function (f) { return f.properties.code === JD_CODE; })[0] || null;
    // 主图：排除九段线，避免把外接框拉到北纬 3.4°
    var feats = all.filter(function (f) { return f.properties.code !== JD_CODE; });

    var cs = window.getComputedStyle(el);
    var W = 760, H = 460, s = 1, ox = 0, oy = 0;
    var pad = 10, bb = bboxOf(feats);
    var jdBB = jd ? bboxOf([jd]) : null;
    var jdS = 1, jdOx = 0, jdOy = 0, jdW = 0, jdH = 0;

    var metric = (opts && opts.metric) || "areas";
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "map");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "中国分省片区分布图");
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

    function layout() {
      W = Math.max(320, Math.round(el.clientWidth - parseFloat(cs.paddingLeft || 0) - parseFloat(cs.paddingRight || 0)));
      H = Math.max(280, Math.round(el.clientHeight - parseFloat(cs.paddingTop || 0) - parseFloat(cs.paddingBottom || 0)));
      s = Math.min((W - pad * 2) / (bb.maxX - bb.minX), (H - pad * 2) / (bb.maxY - bb.minY));
      ox = pad + ((W - pad * 2) - (bb.maxX - bb.minX) * s) / 2;
      oy = pad + ((H - pad * 2) - (bb.maxY - bb.minY) * s) / 2;
      // 南海诸岛附图：右下角小框，单独投影
      if (jd) {
        jdW = Math.min(92, Math.round(W * 0.13));
        jdH = Math.round(jdW * 1.2);
        jdS = Math.min((jdW - 8) / (jdBB.maxX - jdBB.minX), (jdH - 8) / (jdBB.maxY - jdBB.minY));
        jdOx = W - jdW - 10 + ((jdW - 8) - (jdBB.maxX - jdBB.minX) * jdS) / 2 + 4;
        jdOy = H - jdH - 10 + ((jdH - 8) - (jdBB.maxY - jdBB.minY) * jdS) / 2 + 4;
      }
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    }
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

    function tipFor(pr) {
      var na = NA_CODES[pr.code];
      if (na) return '<b>' + esc(pr.name) + "</b><br>不纳入采集范围 · 资料暂缺";
      return "<b>" + esc(pr.name) + "</b><br>在册 " + fmt(pr.areas) +
        "<br>主统计 " + fmt(pr.main) +
        "<br>待核 " + fmt(pr.pending) + "（" + (pr.pending_share || 0) + "%）";
    }

    function draw() {
      maxV = maxOf(metric);
      svg.innerHTML = "";
      feats.forEach(function (f) {
        var pr = f.properties;
        var p = document.createElementNS("http://www.w3.org/2000/svg", "path");
        p.setAttribute("d", pathBuilder(f, bb.minX, bb.maxY, s, ox, oy));
        var na = NA_CODES[pr.code];
        p.setAttribute("class", "p" + (na ? " na" : ""));
        p.setAttribute("tabindex", na ? "-1" : "0");
        p.setAttribute("aria-label", na ? pr.name + "，不纳入采集" :
          pr.name + "，在册 " + (pr.areas || 0) + "，主统计 " + (pr.main || 0) + "，待核 " + (pr.pending || 0));
        p.setAttribute("fill", na ? "none" : palette[bucket(pr[metric] || 0, maxV)]);
        if (!na) {
          var show = function (e) {
            var rect = el.getBoundingClientRect();
            tip.innerHTML = tipFor(pr);
            tip.style.display = "block";
            tip.style.left = Math.min(rect.width - 190, (e.clientX || 0) - rect.left + 14) + "px";
            tip.style.top = Math.max(6, (e.clientY || 0) - rect.top - 10) + "px";
          };
          p.addEventListener("mousemove", show);
          p.addEventListener("focus", function (e) {
            var r2 = p.getBoundingClientRect();
            show({ clientX: r2.left + r2.width / 2, clientY: r2.top + r2.height / 2 });
          });
          p.addEventListener("blur", function () { tip.style.display = "none"; });
          p.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              if (opts && opts.onSelect) opts.onSelect(pr);
              else location.href = "map.html?prov=" + pr.code;
            }
          });
          p.addEventListener("click", function () {
            if (opts && opts.onSelect) opts.onSelect(pr);
            else location.href = "map.html?prov=" + pr.code;
          });
        }
        p.addEventListener("mouseleave", function () { tip.style.display = "none"; });
        svg.appendChild(p);
      });
      // 九段线：独立附图，不可交互
      if (jd) {
        var g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", "jd");
        var box = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        box.setAttribute("x", W - jdW - 10); box.setAttribute("y", H - jdH - 10);
        box.setAttribute("width", jdW); box.setAttribute("height", jdH);
        box.setAttribute("class", "jdbox");
        var d = document.createElementNS("http://www.w3.org/2000/svg", "path");
        d.setAttribute("d", pathBuilder(jd, jdBB.minX, jdBB.maxY, jdS, jdOx, jdOy));
        d.setAttribute("class", "jdline");
        g.appendChild(box);
        g.appendChild(d);
        svg.appendChild(g);
      }
      if (opts && opts.onRedraw) opts.onRedraw();
    }

    draw();
    return {
      el: el,
      setMetric: function (m) { metric = m; draw(); },
      maxOf: maxOf,
      getPalette: function () { return palette; },
      redraw: draw
    };
  }

  /* ---------- 排行榜 ---------- */
  function renderRank(el, metric, rows) {
    var list = rows.slice().sort(function (a, b) { return (b[metric] || 0) - (a[metric] || 0); }).slice(0, 6);
    el.innerHTML = list.map(function (p, i) {
      return '<li data-code="' + esc(p.code) + '" role="button" tabindex="0"><span class="i">' + (i + 1) + "</span>" +
        "<span>" + esc(p.name) + '</span><span class="v">' + fmt(p[metric]) +
        (metric === "pending_share" ? "%" : "") + "</span></li>";
    }).join("");
    $$("li", el).forEach(function (li) {
      var go = function () { location.href = "map.html?prov=" + li.getAttribute("data-code"); };
      li.addEventListener("click", go);
      li.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    });
  }

  /* ---------- 条形图（支持双序列：r.v 深色主条，r.sub 浅色副条） ---------- */
  function renderBars(el, rows) {
    var max = Math.max.apply(null, rows.map(function (r) { return Math.max(r.v, r.sub || 0); }));
    el.innerHTML = rows.map(function (r) {
      var w = max ? (r.v / max) * 100 : 0;
      var w2 = max && r.sub != null ? (r.sub / max) * 100 : 0;
      return '<div class="bar' + (r.zero ? " zero" : "") + '"><span>' + esc(r.label) + '</span><span class="track">' +
        (r.sub != null ? '<span class="fill sub" style="width:' + w2.toFixed(1) + '%"></span>' : "") +
        '<span class="fill' + (r.gold ? " gold" : "") + '" style="width:' + w.toFixed(1) + '%"></span></span>' +
        '<span class="v">' + fmt(r.v) + "</span></div>";
    }).join("");
  }

  /* ---------- 导出 ---------- */
  window.RDKit = { fmt: fmt, esc: esc, buildMap: buildMap, renderRank: renderRank, renderBars: renderBars };

  document.addEventListener("DOMContentLoaded", function () { markNav(); mobileNav(); });
})();
