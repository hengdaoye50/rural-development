/**
 * 构建站点成品：web/ → dist/
 * 只发布站点文件与下载数据，绝不把 data/raw 的证据原文带上线。
 *
 * 用法：node scripts/build-site.mjs
 */
import { cp, mkdir, readdir, rm, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const WEB = path.join(ROOT, "web");
const DIST = path.join(ROOT, "dist");
const MAP = path.join(ROOT, "data", "export", "map");
const SLUG = "rural-development";

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

async function main() {
  await rm(DIST, { recursive: true, force: true });
  await mkdir(DIST, { recursive: true });

  let n = 0;
  for (const file of await listFiles(WEB)) {
    const rel = path.relative(WEB, file).split(path.sep).join("/");
    if (rel.split("/").some((seg) => seg.startsWith("_") || seg.startsWith("."))) continue;
    const dest = path.join(DIST, rel);
    await mkdir(path.dirname(dest), { recursive: true });
    await cp(file, dest);
    n += 1;
  }
  console.log(`web → dist：${n} 个文件`);

  // 下载区：全量数据成品（CSV / GeoJSON）
  const downloads = [
    "provinces.geojson",
    "cities.geojson",
    "分省汇总.csv",
    "分市汇总.csv",
    "分县汇总.csv",
  ];
  let m = 0;
  if (existsSync(MAP)) {
    await mkdir(path.join(DIST, "downloads"), { recursive: true });
    for (const f of downloads) {
      const src = path.join(MAP, f);
      if (!existsSync(src)) continue;
      await cp(src, path.join(DIST, "downloads", f));
      m += 1;
    }
  }
  console.log(`downloads：${m} 个文件`);

  // Cloudflare Pages 用 404 兜底（多页站点）
  if (!existsSync(path.join(DIST, "404.html")) && existsSync(path.join(WEB, "404.html"))) {
    await cp(path.join(WEB, "404.html"), path.join(DIST, "404.html"));
  }

  await writeFile(
    path.join(DIST, ".build-meta"),
    `slug=${SLUG}\nbuilt=${new Date().toISOString()}\nfiles=${n}\n`,
    "utf8",
  );
  console.log("dist 构建完成");
}

main().catch((err) => {
  console.error("构建失败：", err);
  process.exit(1);
});
