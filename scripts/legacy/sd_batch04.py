"""SD 第四/第五批省级片区补采（鲁农组办发〔2026〕14号等）。

只 append，字段与 HEADER 严格对齐。
"""
from __future__ import annotations

import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean\by_province")
RAW = Path(r"D:\CODEX\全国乡村片区化数据库\data\raw\SD")

AREA_FIELDS = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision",
    "status", "lead_org", "issuer", "summary", "parent_area_key",
    "first_source_id", "record_state", "created_at", "updated_at", "created_by",
]
SRC_FIELDS = [
    "source_id", "area_id", "url", "title", "publisher", "published_ymd",
    "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256",
]
MAP_FIELDS = ["area_id", "source_id", "entity_type", "rel"]
REGMAP_FIELDS = ["area_id", "region_code", "role", "is_core"]

SOURCES = {
    "S370211": {
        "url": "https://www.sohu.com/a/1035299857_121106991",
        "title": "东营6片区入选第五批省级乡村振兴片区",
        "publisher": "东营日报/大众网转载",
        "published_ymd": "2026-06-11",
        "excerpt": "鲁农组办发〔2026〕14号公布第五批省级新建乡村振兴片区名单：东营区“魅力城南·乐游六户”、广饶县“莓好颜徐”、垦利区“美郝佳源”、利津县“黄河智果”、黄三角农高区丁庄、河口区新户“绿野·海韵”乡村振兴片区正式获批。",
        "local_path": "data/raw/SD/20260611-dongying-6pianqu/原文.md",
        "cred": "B",
    },
    "S370212": {
        "url": "https://view.inews.qq.com/a/20260608A0AK2F00",
        "title": "德州六个片区，入选省级名单！",
        "publisher": "有德之州/腾讯新闻",
        "published_ymd": "2026-06-08",
        "excerpt": "《第五批省级乡村振兴片区名单》德州六个片区入选。新建：禹城市“幸福河畔 四美梁辛”、齐河县“华店蘑盒”、临邑县“盘龙里·黄河故道”、天衢新区“抬头见喜”。提升：乐陵市杨安、平原县桃园街道乡村振兴片区。",
        "local_path": "data/raw/SD/20260608-dezhou-6pianqu/原文.md",
        "cred": "B",
    },
    "S370213": {
        "url": "https://nyj.weihai.gov.cn/art/2025/6/24/art_164137_5598687.html",
        "title": "我市五个片区入选第四批省级乡村振兴片区",
        "publisher": "威海市农业农村局",
        "published_ymd": "2025-06-24",
        "excerpt": "第四批省级乡村振兴片区名单，威海五个片区入选：荣成市“海牧蓝乡”衔接乡村振兴集中推进区、乳山市“山海胜景·莓好古寨”、文登区昆嵛山生态经济乡村振兴齐鲁样板片区、临港区“金井黄山·清泉康谷”、环翠区“正棋山城乡融合”衔接乡村振兴集中推进区。",
        "local_path": "data/raw/SD/20250624-weihai-5pianqu/原文.md",
        "cred": "A",
    },
}

# (area_id, name, name_norm, type, note, tags, city, county, town, cover, sv, st, ymd, prec, status, lead, issuer, summary, parent, src, batch)
AREAS = [
    ("A370118", "莓好颜徐乡村振兴片区", "莓好颜徐乡村振兴片区", "T04",
     "第五批省级新建；广饶县颜徐；莓果产业", "产业",
     "370500", "370523", "广饶街道", "东营市广饶县颜徐片区，莓果产业", "", "", "2026-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "广饶县“莓好颜徐”乡村振兴片区获批列入鲁农组办发〔2026〕14号第五批省级新建乡村振兴片区名单。",
     "", "S370211", "SD-batch04"),
    ("A370119", "美郝佳源乡村振兴片区", "美郝佳源乡村振兴片区", "T01",
     "第五批省级新建；垦利区郝家", "和美乡村",
     "370500", "370521", "郝家镇", "东营市垦利区郝家镇美郝佳源片区", "", "", "2026-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "垦利区“美郝佳源”乡村振兴片区获批列入第五批省级新建乡村振兴片区名单。",
     "", "S370211", "SD-batch04"),
    ("A370120", "黄河智果乡村振兴片区", "黄河智果乡村振兴片区", "T04",
     "第五批省级新建；利津县；黄河智果品牌", "产业",
     "370500", "370522", "", "东营市利津县黄河智果乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "利津县“黄河智果”乡村振兴片区获批列入第五批省级新建乡村振兴片区名单。",
     "", "S370211", "SD-batch04"),
    ("A370121", "丁庄乡村振兴片区", "丁庄乡村振兴片区", "T01",
     "第五批省级新建；黄三角农高区丁庄", "和美乡村",
     "370500", "370523", "丁庄镇", "黄三角农高区丁庄乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "黄三角农高区丁庄乡村振兴片区获批列入第五批省级新建乡村振兴片区名单。",
     "", "S370211", "SD-batch04"),
    ("A370122", "幸福河畔·四美梁辛乡村振兴片区", "幸福河畔四美梁辛乡村振兴片区", "T01",
     "第五批省级新建；禹城市梁辛", "和美乡村",
     "371400", "371482", "", "德州市禹城市“幸福河畔 四美梁辛”乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "禹城市“幸福河畔 四美梁辛”乡村振兴片区入选第五批省级乡村振兴片区新建名单。",
     "", "S370212", "SD-batch04"),
    ("A370123", "华店蘑盒乡村振兴片区", "华店蘑盒乡村振兴片区", "T04",
     "第五批省级新建；齐河县华店；蘑菇产业", "产业",
     "371400", "371425", "华店镇", "德州市齐河县华店镇“华店蘑盒”乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "齐河县“华店蘑盒”乡村振兴片区入选第五批省级乡村振兴片区新建名单。",
     "", "S370212", "SD-batch04"),
    ("A370124", "盘龙里·黄河故道乡村振兴片区", "盘龙里黄河故道乡村振兴片区", "T05",
     "第五批省级新建；临邑县黄河故道", "农文旅",
     "371400", "371424", "", "德州市临邑县“盘龙里·黄河故道”乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "临邑县“盘龙里·黄河故道”乡村振兴片区入选第五批省级乡村振兴片区新建名单。",
     "", "S370212", "SD-batch04"),
    ("A370125", "抬头见喜乡村振兴片区", "抬头见喜乡村振兴片区", "T01",
     "第五批省级新建；德州天衢新区", "和美乡村",
     "371400", "371400", "", "德州市天衢新区“抬头见喜”乡村振兴片区", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "天衢新区“抬头见喜”乡村振兴片区入选第五批省级乡村振兴片区新建名单。",
     "", "S370212", "SD-batch04"),
    ("A370126", "杨安乡村振兴片区", "杨安乡村振兴片区", "T04",
     "第五批省级提升；乐陵市杨安镇调味品产业", "产业",
     "371400", "371481", "杨安镇", "德州市乐陵市杨安乡村振兴片区（提升片区）", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "乐陵市杨安乡村振兴片区入选第五批省级乡村振兴片区提升名单。",
     "", "S370212", "SD-batch04"),
    ("A370127", "桃园街道乡村振兴片区", "桃园街道乡村振兴片区", "T01",
     "第五批省级提升；平原县桃园街道", "和美乡村",
     "371400", "371426", "桃园街道", "德州市平原县桃园街道乡村振兴片区（提升片区）", "", "", "2026-06", "month", "运行中",
     "", "省农业农村厅",
     "平原县桃园街道乡村振兴片区入选第五批省级乡村振兴片区提升名单。",
     "", "S370212", "SD-batch04"),
    ("A370128", "海牧蓝乡衔接乡村振兴集中推进区", "海牧蓝乡衔接乡村振兴集中推进区", "T06",
     "第四批省级；荣成市；衔接推进区", "帮扶协作",
     "371000", "371082", "", "威海荣成市“海牧蓝乡”衔接乡村振兴集中推进区", "", "", "2025-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "荣成市“海牧蓝乡”衔接乡村振兴集中推进区入选第四批省级乡村振兴片区名单。",
     "", "S370213", "SD-batch04"),
    ("A370129", "山海胜景·莓好古寨片区", "山海胜景莓好古寨片区", "T05",
     "第四批省级；乳山市古寨；莓果+山海文旅", "农文旅",
     "371000", "371083", "", "威海乳山市“山海胜景·莓好古寨”衔接乡村振兴集中推进区", "", "", "2025-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "乳山市“山海胜景·莓好古寨”衔接乡村振兴集中推进区入选第四批省级乡村振兴片区名单。",
     "", "S370213", "SD-batch04"),
    ("A370130", "昆嵛山生态经济乡村振兴齐鲁样板片区", "昆嵛山生态经济乡村振兴齐鲁样板片区", "T01",
     "第四批省级；文登区昆嵛山", "生态;和美乡村",
     "371000", "371003", "", "威海文登区昆嵛山生态经济乡村振兴齐鲁样板片区", "", "", "2025-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "文登区昆嵛山生态经济乡村振兴齐鲁样板片区入选第四批省级乡村振兴片区名单。",
     "", "S370213", "SD-batch04"),
    ("A370131", "金井黄山·清泉康谷乡村振兴齐鲁样板片区", "金井黄山清泉康谷乡村振兴齐鲁样板片区", "T01",
     "第四批省级；威海临港区草庙子镇", "和美乡村",
     "371000", "371002", "草庙子镇", "威海临港区“金井黄山·清泉康谷”乡村振兴齐鲁样板片区", "", "", "2025-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "临港区“金井黄山·清泉康谷”乡村振兴齐鲁样板片区入选第四批省级乡村振兴片区名单。",
     "", "S370213", "SD-batch04"),
    ("A370132", "正棋山城乡融合衔接乡村振兴集中推进区", "正棋山城乡融合衔接乡村振兴集中推进区", "T07",
     "第四批省级；环翠区；城乡融合", "城乡融合",
     "371000", "371002", "", "威海环翠区“正棋山城乡融合”衔接乡村振兴集中推进区", "", "", "2025-06", "month", "运行中",
     "", "省委农办/省农业农村厅/省财政厅",
     "环翠区“正棋山城乡融合”衔接乡村振兴集中推进区入选第四批省级乡村振兴片区名单。",
     "", "S370213", "SD-batch04"),
]


def write_raw(slug: str, src: dict) -> None:
    d = RAW / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(
        '{\n'
        f'  "url": "{src["url"]}",\n'
        f'  "title": "{src["title"]}",\n'
        f'  "publisher": "{src["publisher"]}",\n'
        f'  "published_ymd": "{src["published_ymd"]}",\n'
        '  "fetched_at": "2026-09-30T20:00:00+08:00",\n'
        f'  "cred": "{src["cred"]}",\n'
        '  "hash_sha256": ""\n}\n',
        encoding="utf-8",
    )
    (d / "原文.md").write_text(
        f"# {src['title']}\n\n- 发布者：{src['publisher']}\n"
        f"- 发布日期：{src['published_ymd']}\n- URL：{src['url']}\n\n"
        f"## 正文相关摘录\n\n{src['excerpt']}\n",
        encoding="utf-8",
    )


def append(path: Path, fields: list[str], rows: list[dict]) -> int:
    existing = []
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    have = {r.get(fields[0]) for r in existing}
    added = [r for r in rows if r.get(fields[0]) not in have]
    if not added:
        return 0
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in existing:
            w.writerow({h: (r.get(h) or "") for h in fields})
        for r in added:
            w.writerow({h: (r.get(h) or "") for h in fields})
    return len(added)


def main() -> None:
    for slug, src in [
        ("20260611-dongying-6pianqu", SOURCES["S370211"]),
        ("20260608-dezhou-6pianqu", SOURCES["S370212"]),
        ("20250624-weihai-5pianqu", SOURCES["S370213"]),
    ]:
        write_raw(slug, src)

    src_rows = []
    for sid, s in SOURCES.items():
        src_rows.append({
            "source_id": sid,
            "area_id": AREAS[0][0],  # placeholder; map fixes links
            "url": s["url"], "title": s["title"], "publisher": s["publisher"],
            "published_ymd": s["published_ymd"], "excerpt": s["excerpt"],
            "fetched_at": "2026-09-30T20:00:00+08:00",
            "credibility": s["cred"], "local_path": s["local_path"], "hash_sha256": "",
        })
    # better: one source row per source_id with first related area
    src_by_id = {r["source_id"]: r for r in src_rows}
    for a in AREAS:
        sid = a[20]
        if sid in src_by_id:
            src_by_id[sid]["area_id"] = a[0]
    src_rows = list(src_by_id.values())

    area_rows = []
    for t in AREAS:
        (aid, name, norm, tcode, note, tags, city, county, town,
         cover, sv, st, ymd, prec, status, lead, issuer, summary, parent, sid, batch) = t
        area_rows.append({
            "area_id": aid, "name": name, "name_norm": norm, "type_code": tcode,
            "type_primary_note": note, "tags": tags,
            "province_code": "370000", "city_code": city, "county_code": county,
            "town_codes": town, "cover_desc": cover,
            "scale_villages": sv, "scale_towns": st,
            "founded_ymd": ymd, "founded_precision": prec, "status": status,
            "lead_org": lead, "issuer": issuer, "summary": summary,
            "parent_area_key": parent, "first_source_id": sid,
            "record_state": "active", "created_at": "2026-09-30",
            "updated_at": "2026-09-30", "created_by": batch,
        })

    n = append(BY / "SD-area.csv", AREA_FIELDS, area_rows)
    n += append(BY / "SD-source.csv", SRC_FIELDS, src_rows)
    maps = [{"area_id": r["area_id"], "source_id": r["first_source_id"], "entity_type": "area", "rel": "primary"} for r in area_rows]
    n += append(BY / "SD-area_source_map.csv", MAP_FIELDS, maps)
    regs = []
    for r in area_rows:
        if r["county_code"]:
            regs.append({"area_id": r["area_id"], "region_code": r["county_code"], "role": "county", "is_core": "1"})
    n += append(BY / "SD-area_region_map.csv", REGMAP_FIELDS, regs)
    print("appended", n)


if __name__ == "__main__":
    main()
