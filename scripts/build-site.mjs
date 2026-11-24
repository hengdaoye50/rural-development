/**
 * 构建站点成品：web/ → dist/
 * 只发布站点文件与下载数据，绝不把 data/raw 的证据原文带上线。
 *
 * 用法：node scripts/build-site.mjs
 * 内置断言（不过就退出非零）：下载文件齐全、summary 口径恒等式成立、无残留过期文案。
 */
import { cp, mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const WEB = path.join(ROOT, "web");
const DIST = path.join(ROOT, "dist");
const MAP = path.join(ROOT, "data", "export", "map");
const SLUG = "rural-development";
const ALLOW_UNDERSCORE = new Set(["_headers", "_redirects"]);

async function listFiles(dir) {
  const out = [];
  for (const name of await readdir(dir)) {
    const p = path.join(dir, name);
    const s = await stat(p);
    if (s.isDirectory()) out.push(...(await listFiles(p)));
    else out.push(p);
  }
  return out;
}

function fail(msg) {
  console.error("✗ 构建断言失败：" + msg);
  process.exit(1);
}

async function main() {
  await rm(DIST, { recursive: true, force: true });
  await mkdir(DIST, { recursive: true });

  let n = 0;
  for (const file of await listFiles(WEB)) {
    const rel = path.relative(WEB, file).split(path.sep).join("/");
    const segs = rel.split("/");
    const base = segs[segs.length - 1];
    if (segs.some((s) => s.startsWith("."))) continue;
    if (base.startsWith("_") && !ALLOW_UNDERSCORE.has(base)) continue; // 临时文件不发布
    const dest = path.join(DIST, rel);
    await mkdir(path.dirname(dest), { recursive: true });
    await cp(file, dest);
    n += 1;
  }
  console.log(`web → dist：${n} 个文件`);

  // 下载区：全量数据成品（CSV / GeoJSON）——缺一个就失败，不静默跳过
  const downloads = [
    "provinces.geojson",
    "cities.geojson",
    "分省汇总.csv",
    "分市汇总.csv",
    "分县汇总.csv",
  ];
  const missing = downloads.filter((f) => !existsSync(path.join(MAP, f)));
  if (missing.length) fail(`下载文件缺失：${missing.join("、")}（先跑 scripts/export_map_data.py）`);
  await mkdir(path.join(DIST, "downloads"), { recursive: true });
  for (const f of downloads) {
    await cp(path.join(MAP, f), path.join(DIST, "downloads", f));
  }
  console.log(`downloads：${downloads.length} 个文件`);

  // 口径恒等式：summary.js 必须自洽，否则宁可不上线
  const summaryPath = path.join(WEB, "assets", "data", "summary.js");
  if (!existsSync(summaryPath)) fail("web/assets/data/summary.js 不存在");
  const raw = await readFile(summaryPath, "utf8");
  const json = JSON.parse(raw.replace(/^window\.RD\s*=\s*/, "").replace(/;\s*$/, ""));
  const T = json.totals, G = json.groups || {};
  const checks = [
    ["macro = areas + belt", T.macro === T.areas + T.belt],
    ["main = A + B", T.main === (G.A || 0) + (G.B || 0)],
    ["wide = main + C", T.wide === T.main + (G.C || 0)],
    ["areas − pending = A+B+C+D+E",
      T.areas - T.pending === (G.A || 0) + (G.B || 0) + (G.C || 0) + (G.D || 0) + (G.E || 0)],
  ];
  const bad = checks.filter((c) => !c[1]).map((c) => c[0]);
  if (bad.length) fail("summary 口径不自洽：" + bad.join("；"));
  console.log(`口径断言：${checks.length} 条全部通过（在册 ${T.areas}｜主统计 ${T.main}｜待核 ${T.pending}）`);

  // 过期文案守卫
  const stale = [
    ["index.html", "E 组当前归零"],
    ["index.html", "31 个省级单位 ·"],
    ["about.html", "607 个有片区的县"],
  ];
  for (const [f, needle] of stale) {
    const p = path.join(DIST, f);
    if (existsSync(p) && (await readFile(p, "utf8")).includes(needle)) {
      fail(`${f} 仍含过期文案「${needle}」`);
    }
  }

  if (!existsSync(path.join(DIST, "404.html"))) fail("dist/404.html 缺失");

  // 静态资源版本号：HTML 里的 assets/*.css|js 统一加 ?v=<stamp>，
  // 避免「HTML 已更新、JS 还在浏览器缓存里」导致的功能错配
  const stamp = new Date().toISOString().slice(0, 19).replace(/[-T:]/g, "");
  let stamped = 0;
  for (const f of await listFiles(DIST)) {
    if (!f.endsWith(".html")) continue;
    let html = await readFile(f, "utf8");
    const before = html;
    html = html.replace(/(href|src)="(assets\/[^"?]+\.(?:css|js))"/g, (m, a, u) => {
      stamped += 1;
      return `${a}="${u}?v=${stamp}"`;
    });
    if (html !== before) await writeFile(f, html, "utf8");
  }
  console.log(`资源版本号：${stamped} 处 → v=${stamp}`);

  await writeFile(
    path.join(DIST, ".build-meta"),
    `slug=${SLUG}\nbuilt=${new Date().toISOString()}\nfiles=${n}\ndownloads=${downloads.length}\nareas=${T.areas}\n`,
    "utf8",
  );
  console.log("dist 构建完成");
}

main().catch((err) => {
  console.error("构建失败：", err);
  process.exit(1);
});
