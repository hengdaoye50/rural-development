# -*- coding: utf-8 -*-
"""通用「名单 OCR 文本 → media roster 候选表」解析器（省级/市级名单共用）。

背景：省级/市级片区名单常以**长图**发布（公众号或政府网页图片），先由
`scripts/wechat_ocr_images.py`（公众号）或 `scripts/ocr_pdf.py`（PDF 扫描件）识别成文本，
再由本脚本抽成 `data/stage/candidates/area-media-roster-{ABBR}.csv`，
交给 `scripts/ingest_area_media_roster.py {ABBR}` 建档（`status=待核`，进 M 层不进主统计）。

解析逻辑（不猜、只抽）：
  1. **市级表头**：`1.济南市` / `一、济南市` / `济南市（8个）` → 切换当前市；
     市名与 `region` 里该省的地级行比对（自治州取「恩施」这类短名）。
  2. **阶段表头**：`新建片区` / `提升片区` / `创建名单` …（可用 profile 的 phase_words 扩展）。
  3. **条目行**：含「片区」且能以**县区名开头**（或功能区别名开头，或尾部括注县区）→
     县区码 + 片区名。县区按「市级前缀 + 名称」双匹配（防枣庄市中区错配济南）。
  4. 解析不出的行进 `roster-parse-rejects-{ABBR}.csv`，**不猜县区、不猜名字**。

输入 profile（可选，JSON，`data/stage/candidates/roster-profile-{ABBR}.json`）：
```json
{
  "roster_label": "河北省省级和美乡村重点片区",
  "issuer": "河北省农业农村厅",
  "published_ymd": "2025-04-03",
  "founded_ymd": "2025-04",
  "founded_precision": "month",
  "parent_area_key": "河北省省级和美乡村重点片区",
  "phase_words": ["新建", "提升", "创建", "新增", "培育"],
  "aliases": {"西海岸新区": "370211"},
  "default_phase": "新建"
}
```
profile 可省；省码取自内置表，URL/标题缺省从 OCR 目录的 `meta.json` 读。

用法：
  python scripts/parse_roster_ocr.py --abbr SD --ocr data/raw/SD/xxx/ocr.md
  python scripts/parse_roster_ocr.py --abbr HB --ocr data/raw/HB/xxx/ocr.md --profile data/stage/candidates/roster-profile-HB.json
  python scripts/parse_roster_ocr.py --abbr SD --ocr ... --dry-run     # 只统计不写盘
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
CAND = ROOT / "data" / "stage" / "candidates"

PROV = {
    "BJ": "110000", "TJ": "120000", "HE": "130000", "SX": "140000", "NM": "150000",
    "LN": "210000", "JL": "220000", "HL": "230000", "SH": "310000", "JS": "320000",
    "ZJ": "330000", "AH": "340000", "FJ": "350000", "JX": "360000", "SD": "370000",
    "HA": "410000", "HB": "420000", "HN": "430000", "GD": "440000", "GX": "450000",
    "HI": "460000", "CQ": "500000", "SC": "510000", "GZ": "520000", "YN": "530000",
    "XZ": "540000", "SN": "610000", "GS": "620000", "QH": "630000", "NX": "640000",
    "XJ": "650000",
}
MUNICIPALITY = {"BJ", "TJ", "SH", "CQ"}

COLS = ["name", "type_code", "city_code", "county_code", "cover_desc", "status", "founded_ymd",
        "founded_precision", "issuer", "summary", "source_url", "source_title", "publisher",
        "published_ymd", "note", "parent_area_key", "local_path", "credibility", "excerpt",
        "scale_villages", "tags"]

PUNCT = re.compile(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-－]+")
NUM_HEAD = re.compile(r"^\s*(?:[（(]?\d{1,3}[)）.、．]|[一二三四五六七八九十]{1,3}[、.．])\s*")
NOISE = re.compile(
    r"^(?:附件|名单|公示|公告|通知|来源|编辑|审核|排版|制图|扫一扫|扫描|长按|点击|关注|阅读|"
    r"公众号|微信号|标题|图\s*\d|第[一二三四五六七八九十\d]+批|.*?(?:名单|公示|通知)$)")
CITY_TAIL = re.compile(r"^(?P<name>.{2,12}?)(?:市|州|地区|盟)(?:（[^）]*）|\([^)]*\))?$")
AREA_SUFFIX = "片区"
AREA_WORDS = re.compile(r"片区|示范片|体验区|示范区")


def read_csv(p: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not p.exists():
        return [], []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write_csv(p: Path, hdr: list[str], rows: list[dict[str, str]]) -> None:
    """原子写：临时文件 + os.replace；写前断言字段 ⊆ 表头。"""
    p.parent.mkdir(parents=True, exist_ok=True)
    for r in rows:
        extra = set(r) - set(hdr)
        assert not extra, f"字段超出表头：{extra}"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).strip()


def short_city(name: str) -> list[str]:
    """地级名 → 可匹配短名：去掉 市/地区/盟；自治州取族名前的部分。"""
    out = []
    n = (name or "").strip()
    if not n:
        return out
    out.append(n)
    base = re.sub(r"(市|地区|盟)$", "", n)
    if base != n:
        out.append(base)
    m = re.match(r"^(.+?)(?:蒙古族|藏族|彝族|苗族|侗族|哈尼族|布依族|土家族|白族|傣族|景颇族|傈僳族|回族|朝鲜族|柯尔克孜|哈萨克|维吾尔)?(?:自治州|州)$", n)
    if m and m.group(1) and m.group(1) not in out:
        out.append(m.group(1))
    return [x for x in dict.fromkeys(out) if len(x) >= 2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--abbr", required=True, help="2 字母省码，如 SD/HB/HE")
    ap.add_argument("--ocr", required=True, help="OCR 文本路径（ocr.md / 原文.md）")
    ap.add_argument("--profile", default="", help="profile JSON（可选）")
    ap.add_argument("--out", default="", help="输出 CSV（缺省 area-media-roster-{ABBR}.csv）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    abbr = args.abbr.upper()
    ocr_path = Path(args.ocr)
    if not ocr_path.is_absolute():
        ocr_path = (ROOT / ocr_path).resolve()
    if not ocr_path.is_file():
        print(f"找不到 OCR 文本：{ocr_path}")
        return 1
    prov_code = PROV.get(abbr)
    if not prov_code:
        print(f"未知省码 {abbr}")
        return 2

    prof: dict = {}
    if args.profile:
        prof = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    else:
        default_prof = CAND / f"roster-profile-{abbr}.json"
        if default_prof.exists():
            prof = json.loads(default_prof.read_text(encoding="utf-8"))
    phases = prof.get("phase_words") or ["新建", "提升", "创建", "新增", "培育", "续建"]
    aliases = {k: v for k, v in (prof.get("aliases") or {}).items()}

    meta = {}
    for mp in sorted(ocr_path.parent.glob("meta.json")):
        try:
            meta = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            meta = {}
    source_url = prof.get("source_url") or meta.get("url") or meta.get("primary_url") or ""
    source_title = prof.get("source_title") or meta.get("title", ocr_path.parent.name)
    publisher = prof.get("publisher") or meta.get("publisher", "微信公众号")
    published_ymd = prof.get("published_ymd") or meta.get("published_ymd", "")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows_reg = [dict(r) for r in con.execute(
        "select region_code, name, parent_code, level from region where region_code like ?",
        (prov_code[:2] + "%",))]
    con.close()
    city_rows = [r for r in rows_reg if r["level"] == "city"]
    county_rows = [r for r in rows_reg if r["level"] == "county"]
    # 直辖市/无地级行时：用省级本身当市
    city_map: dict[str, str] = {}
    if abbr in MUNICIPALITY or not city_rows:
        prov_name = next((r["name"] for r in rows_reg if r["region_code"] == prov_code), "")
        for k in short_city(prov_name):
            city_map[k] = prov_code
    for r in city_rows:
        for k in short_city(r["name"]):
            city_map.setdefault(k, r["region_code"])
    city_keys = sorted(city_map, key=len, reverse=True)
    county_by_city: dict[str, list[dict]] = {}
    for r in county_rows:
        county_by_city.setdefault(r["parent_code"], []).append(r)
    for lst in county_by_city.values():
        lst.sort(key=lambda x: len(x["name"] or ""), reverse=True)
    alias_keys = sorted(aliases, key=len, reverse=True)

    lines = ocr_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    rel_ocr = ocr_path.relative_to(ROOT).as_posix() if ocr_path.is_relative_to(ROOT) else str(ocr_path)
    # 一段话里用顿号串列多个片区（「A片区、B片区、C片区11个入选」）→ 拆成独立条目
    units: list[tuple[str, int]] = []
    for li, raw in enumerate(lines):
        ln = norm(raw)
        if ln and len(AREA_WORDS.findall(ln)) >= 3:
            units += [(seg, li) for seg in re.split(r"[、，,；;。]", ln) if seg.strip()]
        else:
            units.append((raw, li))
    county_parent = {r["region_code"]: r["parent_code"] for r in county_rows}

    items, rejects = [], []
    city, phase = "", prof.get("default_phase", "")
    section_county = ""
    cur_item: int | None = None
    consumed: set[int] = set()      # 已被当作「县区行」消费的单元（潍坊式：片区名一行、县区名下一行）

    def match_county(token: str, city_code: str) -> str:
        for r in (county_by_city.get(city_code, []) if city_code else []):
            if (r["name"] or "") and token.startswith(r["name"]):
                return r["region_code"]
        # 全省范围：命中必须唯一（同名县区如鼓楼区不予猜）
        hits = list(dict.fromkeys(r["region_code"] for r in county_rows
                                  if (r["name"] or "") and token.startswith(r["name"])))
        return hits[0] if len(hits) == 1 else ""

    for i, (u_raw, li) in enumerate(units):
        if i in consumed:
            continue
        line = norm(u_raw)
        if not line or line.startswith("#"):
            continue
        s = line.replace("*", "").strip()
        # 0) 村数行（核心村/组团村…）：记到上一个条目
        mv = re.match(r"^(核心村|组团村|覆盖村|涉及村)[:：](.+)$", s)
        if mv and cur_item is not None:
            names = [x for x in re.split(r"[、,，;；]", mv.group(2)) if x.strip()]
            if names:
                items[cur_item]["_villages"] = items[cur_item].get("_villages", 0) + len(names)
                items[cur_item]["_village_txt"] = (items[cur_item].get("_village_txt", "") +
                                                   "；" + s).strip("；")
            continue
        # 1) 市级表头
        head = NUM_HEAD.sub("", s)
        m = CITY_TAIL.match(head)
        if m:
            tok = m.group("name")
            hit_city = ""
            for k in city_keys:
                if tok == k or tok.startswith(k) or k.startswith(tok):
                    hit_city = city_map[k]
                    break
            if hit_city:
                city, section_county, cur_item = hit_city, "", None
                continue
        # 2) 阶段表头
        p2 = NUM_HEAD.sub("", s).rstrip("：: ")
        hit = next((p for p in phases if p2 == p or p2 == p + AREA_SUFFIX or
                    (p2.startswith(p) and len(p2) <= len(p) + 4 and AREA_SUFFIX in p2)), "")
        if hit:
            phase = hit
            continue
        # 3) 县区小节标题：【西湖区】 / 单独的「西湖区」
        sec = re.sub(r"[（(]\d+个[)）]$", "", NUM_HEAD.sub("", s).strip("【】[] ")).strip()
        if (s.startswith("【") and s.endswith("】")) or (2 <= len(sec) <= 9 and
                                                       sec.endswith(("区", "县", "市", "旗"))):
            cc = match_county(sec, city)
            if cc:
                section_county, cur_item = cc, None
                continue
        # 4) 条目行
        if not AREA_WORDS.search(s) or len(s) > 90:
            continue
        if NOISE.match(s):
            continue
        body = NUM_HEAD.sub("", s).strip("。． .、")
        tag = ""
        if re.search(r"[:：]", body):
            left, right = re.split(r"[:：]", body, maxsplit=1)
            # 只把「名称：分类」拆开；「具体为：南漳县…」这类引导语只丢引导语
            if AREA_WORDS.search(left) and 3 <= len(left.strip()) <= 40 and 2 <= len(right.strip()) <= 20:
                body, tag = left.strip(), right.strip()
            elif len(left.strip()) <= 8 and right.strip():
                body = right.strip()
        # 尾缀裁剪：「…片区11个片区入选」「…片区等」
        mt2 = re.search(r"(片区)(\d+个|入选|上榜|等|[）)]|$)", body)
        if mt2 and mt2.end(1) < len(body):
            body = body[:mt2.end(1)]
        scale = ""
        ms = re.search(r"[（(]([^（）()]{1,14}?(?:个村|个行政村|个自然村|个乡镇|个街道|个))[)）]$", body)
        if ms:
            scale = ms.group(1)
            body = body[: ms.start()]
        # 末尾括注（村/社区清单）：丢括注、留作覆盖范围描述
        paren = ""
        mpar = re.search(r"[（(]([^（）()]{2,40})[)）]$", body)
        if mpar:
            paren = mpar.group(1)
            body = body[: mpar.start()]
        if len(body) < 4 or not re.search(r"(片区(?:组团)?|示范片|体验区|示范区)$", body):
            continue
        if re.search(r"等\d+个", body):     # 「XX等23个片区入选」是概述句，不是条目
            continue
        county_code, alias_hit = "", ""
        # 4a) 条目自带市名（河北式：秦皇岛市北戴河区全域和美乡村重点片区）
        #     只认带「市/州/盟」的全称，避免把「东营区」剥成「区」
        for k in city_keys:
            if not k.endswith(("市", "州", "盟", "地区")):
                continue
            if body.startswith(k) and len(body) > len(k) + 2:
                city = city_map[k]
                body = body[len(k):]
                section_county = ""
                break
        # 4b) 县区前缀
        for r in (county_by_city.get(city, []) or county_rows):
            cn = r["name"] or ""
            if cn and body.startswith(cn):
                county_code, body = r["region_code"], body[len(cn):]
                break
        # 4c) 继承小节县区
        if not county_code and section_county:
            county_code = section_county
        # 4c2) 下一行是纯县区名（潍坊光荣册式：片区名一行、县区名下一行）
        if not county_code:
            for j in (i + 1, i + 2):
                if j >= len(units) or j in consumed:
                    continue
                tok = norm(units[j][0]).replace("*", "").strip("【】[] ")
                if not (2 <= len(tok) <= 9 and tok.endswith(("区", "县", "市", "旗"))):
                    continue
                cc = match_county(tok, city)
                if cc:
                    county_code = cc
                    consumed.add(j)
                    break
        # 4d) 功能区别名
        if not county_code:
            for k in alias_keys:
                if body.startswith(k):
                    county_code, alias_hit, body = aliases[k], k, body[len(k):]
                    break
        # 4e) 尾部括注县区（XX片区（XX县））
        if not county_code:
            mp = re.search(r"[（(](.+?[区县市旗])[)）]$", body)
            if mp:
                cc = match_county(mp.group(1), city)
                if cc:
                    county_code, body = cc, body[: mp.start()]
        body = "".join(c for c in body if c not in "\u201c\u201d\u2018\u2019\"'").strip()
        if county_code and not city:
            city = county_parent.get(county_code, "")
        if not county_code:
            rejects.append({"line_no": li + 1, "text": line, "reason": "县区未解析"})
            cur_item = None
            continue
        parts = ["".join(c for c in p if c not in "\u201c\u201d\u2018\u2019\"'").strip("。.．")
                 for p in body.split("、") if p.strip()]
        kicker = f"{phase}" if phase else ""
        cover_base = "；".join([x for x in [prof.get("roster_label", ""), kicker] if x])
        cover = (cover_base + "；" if cover_base else "") + f"OCR原文：{s}"
        if tag:
            cover += f"；分类：{tag}"
        if scale:
            cover += f"；范围：{scale}"
        if paren:
            cover += f"；括注：{paren}"
        # excerpt 取「连续原文行」，保证能在快照里逐字命中（verbatim）
        start = li
        while start > 0 and (li - start) < 10:
            seg = "\n".join(lines[start:li + 1]).strip()
            if len(seg) >= 40:
                break
            start -= 1
        excerpt = "\n".join(lines[max(0, start):li + 1]).strip()
        added = False
        for part in parts:
            if len(part) < 3 or not re.search(r"(片区(?:组团)?|示范片|体验区|示范区)$", part):
                continue
            items.append({
                "name": part, "type_code": prof.get("type_code", "T01"),
                "city_code": city, "county_code": county_code,
                "cover_desc": cover, "status": "待核",
                "founded_ymd": prof.get("founded_ymd", ""),
                "founded_precision": prof.get("founded_precision", "unknown"),
                "issuer": prof.get("issuer", ""),
                "summary": f"{prof.get('roster_label', abbr)}｜{s}"[:200],
                "source_url": source_url, "source_title": source_title, "publisher": publisher,
                "published_ymd": published_ymd,
                "note": "公众号/长图 OCR，待 .gov.cn 原文升级" + (f"；功能区按邻近县区码记录（{alias_hit}）" if alias_hit else ""),
                "parent_area_key": prof.get("parent_area_key", ""),
                "local_path": rel_ocr, "credibility": prof.get("credibility", "C"),
                "excerpt": excerpt, "_phase": phase, "_villages": 0, "tags": tag,
            })
            cur_item = len(items) - 1
            added = True
        if not added:
            rejects.append({"line_no": li + 1, "text": line, "reason": "名称不合规"})
            cur_item = None

    for r in items:
        v = int(r.get("_villages") or 0)
        if v > 0:
            r["scale_villages"] = str(v)
            if r.get("_village_txt"):
                r["cover_desc"] += f"；{r['_village_txt']}"
    seen, uniq = set(), []
    for r in items:
        k = (r["county_code"], PUNCT.sub("", r["name"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)

    from collections import Counter
    by_city = Counter(r["city_code"] for r in uniq)
    by_phase = Counter(r["_phase"] or "(未标注)" for r in uniq)
    total = len(items)
    print(f"{abbr} 解析：条目 {total} 行 → 去重 {len(uniq)} 条；未解析 {len(rejects)} 行")
    print(f"  按市条数：{dict(by_city)}")
    print(f"  阶段分布：{dict(by_phase)}")
    uniq = [{k: v for k, v in r.items() if not k.startswith("_")} for r in uniq]
    for rj in rejects[:10]:
        print(f"  ? L{rj['line_no']} {rj['text'][:44]} | {rj['reason']}")
    if total == 0:
        print("没有解析出条目，检查 OCR 文本或 profile")
        return 1
    out = Path(args.out) if args.out else CAND / f"area-media-roster-{abbr}.csv"
    if not out.is_absolute():
        out = (ROOT / out).resolve()
    if rejects:
        # 与候选表同名，避免同省多份名单互相覆盖 rejects
        rp = out.parent / f"{out.stem}-rejects.csv"
        if not args.dry_run:
            write_csv(rp, ["line_no", "text", "reason"], rejects)
            print(f"  未解析清单 -> {rp.relative_to(ROOT)}")
    if args.dry_run:
        print("dry-run，未写盘")
        return 0
    write_csv(out, COLS, uniq)
    print(f"  -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print(f"接着跑：python scripts/ingest_area_media_roster.py {abbr} --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
