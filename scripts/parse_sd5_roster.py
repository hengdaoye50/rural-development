# -*- coding: utf-8 -*-
"""把公众号 OCR 的「第五批省级乡村振兴片区名单」解析成 media roster 候选表。

输入：data/raw/SD/*wx-img*/ocr.md
输出：data/stage/candidates/area-media-roster-SD.csv（供 ingest_area_media_roster.py SD）

解析规则：
  - `N.XX市` → 当前市；`新建片区` / `提升片区` → setup 形态（写入 cover_desc）
  - 名单行形如 `济阳区“河畔乡居·柿满田园”乡村振兴片区` 或 `西海岸新区张家楼乡村振兴片区`
  - 县区名 = 引号前 / 后缀「乡村振兴片区」前的前缀；去掉「区/县/市/旗」前的县级名做匹配
  - 跳过噪声行（附件、标题、公众号·农畔、页码）
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "data" / "stage" / "candidates" / "area-media-roster-SD.csv"
COLS = ["name", "type_code", "city_code", "county_code", "cover_desc", "status", "founded_ymd",
        "founded_precision", "issuer", "summary", "source_url", "source_title", "publisher",
        "published_ymd", "note", "parent_area_key"]
CITY = {"济南": "370100", "青岛": "370200", "淄博": "370300", "枣庄": "370400", "东营": "370500",
        "烟台": "370600", "潍坊": "370700", "济宁": "370800", "泰安": "370900", "威海": "371000",
        "日照": "371100", "临沂": "371300", "德州": "371400", "聊城": "371500", "滨州": "371600",
        "菏泽": "371700"}
# 功能区别名：官方名单里常见、但 region 无独立县级码；按邻近县区码记录并在 note 注明
ALIAS = {
    "南部山区": "370112",      # 济南南部山区管委会（历城区）
    "西海岸新区": "370211",    # 黄岛区
    "黄三角农高区": "370523",  # 广饶县（丁庄街道）
    "黄渤海新区": "370614",    # 蓬莱区
    "泰山景区": "370902",      # 泰山区（泰山景区代管乡镇）
    "高技术产业开发区": "371002",  # 环翠区
    "临港区": "371002",        # 环翠区（临港经开区）
    "天衢新区": "371402",      # 德城区
    "经济技术开发区": "371602",  # 滨城区
}


def alias_code(tok: str) -> str:
    for k, v in ALIAS.items():
        if tok.startswith(k):
            return v
    return ""


NOISE = re.compile(r"附件|名单|公众号|农畔|扫|关注|第.批|^\d+$|^[\d—\-]+$|片区建设|新建片区|提升片区|^[a-zA-Z]+$")
AREA = re.compile(r"^(.+?)“(.+?)”乡村振兴片区$")
AREA2 = re.compile(r"^(.+?)(乡村振兴片区)$")


def read(p: Path):
    with p.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p: Path, hdr, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    tmp.replace(p)


def main() -> int:
    files = sorted((ROOT / "data" / "raw" / "SD").glob("*wx-img*/ocr.md"))
    if not files:
        print("没有 ocr.md")
        return 1
    ocr = files[-1].read_text(encoding="utf-8")
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    county_rows = [dict(r) for r in con.execute(
        "select region_code, name, parent_code from region where level='county'")]

    def find_county(city_code: str, token: str) -> str:
        token = token.strip()
        for r in county_rows:
            if r["parent_code"] == city_code and r["name"] and token.startswith(r["name"]):
                return r["region_code"]
        # 退化：截取到「区/县/市/旗」为止
        m = re.match(r"(.+?[区县市旗])", token)
        if m:
            short = m.group(1)
            for r in county_rows:
                if r["parent_code"] == city_code and r["name"] == short:
                    return r["region_code"]
        return ""

    url = ""
    meta = sorted((ROOT / "data" / "raw" / "SD").glob("*wx-img*/meta.json"))
    if meta:
        import json
        url = json.loads(meta[-1].read_text(encoding="utf-8")).get("url", "")

    rows, city, phase = [], "", "新建"
    for line in ocr.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^\d+\.(.+?)市$", s)
        if m and m.group(1) in CITY:
            city = CITY[m.group(1)]
            continue
        if s.startswith("新建"):
            phase = "新建"
            continue
        if s.startswith("提升"):
            phase = "提升"
            continue
        if NOISE.search(s) or not s.endswith("乡村振兴片区"):
            continue
        mm = AREA.match(s)
        if mm:
            county_tok, title = mm.group(1), mm.group(2)
        else:
            mm2 = AREA2.match(s)
            base = mm2.group(1) if mm2 else s
            # 无引号：尾部是名称，前部是县区
            mt = re.match(r"^(.+?[区县市旗])(.+)$", base)
            if not mt:
                continue
            county_tok, title = mt.group(1), mt.group(2)
        cc = find_county(city, county_tok) or alias_code(county_tok)
        if not cc:
            print("  ? 县区未解析:", s[:40], "|", county_tok)
            continue
        rows.append({
            "name": title + "乡村振兴片区", "type_code": "T01", "city_code": city,
            "county_code": cc, "status": "待核", "founded_ymd": "2026-06", "founded_precision": "month",
            "issuer": "中共山东省委农村工作领导小组办公室、省农业农村厅、省财政厅",
            "cover_desc": f"第五批省级乡村振兴片区（{phase}片区）；公众号长图 OCR：{s}",
            "summary": f"山东省第五批省级乡村振兴片区（{phase}）｜{s}",
            "source_url": url, "source_title": "【喜报】第五批省级乡村振兴片区建设名单公示（附件长图）",
            "publisher": "美丽东营/农畔（微信公众号）", "published_ymd": "2026-06-03",
            "note": f"公众号长图 OCR，待 .gov.cn 原文升级；{phase}片区" + ("；功能区按邻近县区码记录" if county_tok in ALIAS or alias_code(county_tok) else ""), "parent_area_key": "山东第五批省级片区",
        })
    # 去重（同县同名）
    seen, uniq = set(), []
    for r in rows:
        k = (r["county_code"], re.sub(r"\W", "", r["name"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    write(OUT, COLS, uniq)
    print(f"解析 {len(rows)} 条 -> 去重后 {len(uniq)} 条 -> {OUT.relative_to(ROOT)}")
    from collections import Counter
    print("按市:", dict(Counter(r["city_code"] for r in uniq)))
    print("按阶段:", dict(Counter('提升' if '提升片区' in r['cover_desc'] else '新建' for r in uniq)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
