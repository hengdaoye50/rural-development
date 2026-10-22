"""Add newly discovered named片区 from 2026-09 山东宣传网 + 浙江指导意见."""
from __future__ import annotations

import csv
from pathlib import Path

BY = Path(r"D:\CODEX\全国乡村片区化数据库\data\clean" ) / "by_province"

AREA_FIELDS = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision", "status",
    "lead_org", "issuer", "summary", "parent_area_key", "first_source_id",
    "record_state", "created_at", "updated_at", "created_by",
]
SRC_FIELDS = [
    "source_id", "area_id", "url", "title", "publisher", "published_ymd",
    "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256",
]
MAP_FIELDS = ["area_id", "source_id", "entity_type", "rel"]
REGMAP_FIELDS = ["area_id", "region_code", "role", "is_core"]

SD_SRC = {
    "source_id": "S370200",
    "area_id": "A370070",
    "url": "https://www.sdxc.gov.cn/jzyl/ztxcsy/202609/t20260922_18141933.htm",
    "title": "片区化推进乡村振兴，山东各地这么干",
    "publisher": "山东宣传网/大众日报",
    "published_ymd": "2026-09-22",
    "excerpt": "济南建设省市县三级乡村振兴片区85个、覆盖村庄887个；滨州建成省市县三级片区83个；聊城创建省市县三级片区101个；潍坊组建154个乡村振兴片区覆盖1666个村庄；东营规划建设20个省级、33个市级、17个县级片区。",
    "fetched_at": "2026-09-30T19:00:00+08:00",
    "credibility": "A",
    "local_path": "data/raw/SD/20260922-shandong-gedizhemeigan/原文.md",
    "hash_sha256": "",
}

# 新增：文中具名、库内尚无
NEW_SD = [
    dict(
        area_id="A370070", name="粮安商河·全域和美片区", name_norm="粮安商河全域和美片区",
        type_code="T04", type_primary_note="商河县玉皇庙镇10个自然村；一朵蘑菇一颗豆子一粒麦子",
        tags="产业",
        province_code="370000", city_code="370100", county_code="370126", town_codes="玉皇庙镇",
        cover_desc="济南市商河县玉皇庙镇10个自然村，粮菌豆特色产业链",
        scale_villages="10", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="玉皇庙镇党委", issuer="济南市委农办",
        summary="段家村位于商河县“粮安商河·全域和美”片区，覆盖玉皇庙镇10个自然村，深挖蘑菇、豆子、麦子土特产资源，成立区域性农事服务中心服务周边20余村。",
        parent_area_key="", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370071", name="张家楼乡村振兴片区", name_norm="张家楼乡村振兴片区",
        type_code="T05", type_primary_note="青岛西海岸张家楼街道；1+1+N运营；强村共富公司",
        tags="农文旅;产业",
        province_code="370000", city_code="370200", county_code="370211", town_codes="张家楼街道",
        cover_desc="青岛西海岸新区张家楼街道，以6村左右为单元连片打造",
        scale_villages="", scale_towns="1",
        founded_ymd="2022-01-01", founded_precision="year", status="运行中",
        lead_org="张家楼街道党工委", issuer="青岛市委农办",
        summary="2022年以来青岛以6个左右人文相近、产业相融村庄为单元连片打造乡村振兴片区。张家楼成立乡村振兴联营俱乐部和“1+1+N”运营架构（主运营团队+强村共富公司+N共建方阵），带动1500余名村民增收6750余万元。",
        parent_area_key="QD-pianqu", first_source_id="S370200", record_state="active",
        created_at="2022-01-01", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370072", name="汀罗片区", name_norm="汀罗片区",
        type_code="T04", type_primary_note="利津县汀罗镇盐碱地新型农业田园综合体核心；12村",
        tags="产业",
        province_code="370000", city_code="370500", county_code="370522", town_codes="汀罗镇",
        cover_desc="东营市利津县汀罗镇，盐碱地棉花/粮食，覆盖12个村",
        scale_villages="12", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="汀罗镇党委", issuer="东营市委农办",
        summary="汀罗片区是东营打造盐碱地新型农业田园综合体的核心载体，覆盖12个村；林家屋子片区12个自然村1.6万亩土地一次性流转13年。东营规划建设20个省级、33个市级、17个县级片区，覆盖40%村庄。",
        parent_area_key="DY-sanjipianqu", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370073", name="齐风湖韵乡村振兴片区", name_norm="齐风湖韵乡村振兴片区",
        type_code="T01", type_primary_note="桓台县起凤镇6村；马踏湖生态；草苇编产业",
        tags="产业;文旅",
        province_code="370000", city_code="370300", county_code="370321", town_codes="起凤镇",
        cover_desc="淄博市桓台县起凤镇6个村，马踏湖生态修复+草苇编+文旅",
        scale_villages="6", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="起凤镇党委", issuer="淄博市委农办",
        summary="起凤镇打造“齐风湖韵”乡村振兴片区，统筹6个村构建生态修复、产业集聚、文旅融合、联村共富格局。草苇编产业年产值突破1亿元，从业人员超4000人，辐射周边30多个村。",
        parent_area_key="", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370074", name="马坡村共富茶仓跨村联建片区", name_norm="马坡村共富茶仓跨村联建片区",
        type_code="T02", type_primary_note="莒县夏庄镇6村跨村联建；茶仓统一收加销",
        tags="党建;产业",
        province_code="370000", city_code="371100", county_code="371122", town_codes="夏庄镇",
        cover_desc="日照市莒县夏庄镇大窝疃、南马坡、小窝疃等6个村",
        scale_villages="6", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="夏庄镇党委", issuer="日照市委农办",
        summary="整合大窝疃村、南马坡村、小窝疃村等6个村落资源，组建马坡村共富茶仓“跨村联建”片区，推行基地联建+茶园托管+电商助农，片区内各村集体年均增收5万元。",
        parent_area_key="", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370075", name="文脉卢山·果韵密州乡村振兴片区", name_norm="文脉卢山果韵密州乡村振兴片区",
        type_code="T04", type_primary_note="诸城密州街道3社区6网格；林果链主企业",
        tags="产业",
        province_code="370000", city_code="370700", county_code="370782", town_codes="密州街道",
        cover_desc="潍坊诸城市密州街道3个社区6个网格，苹果/酸枣/板栗产业链",
        scale_villages="", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="密州街道党工委", issuer="潍坊市委农办",
        summary="“文脉卢山·果韵密州”乡村振兴片区锚定林果资源，以链主企业启丰食品为纽带，打通基地种植—就地加工—多元销售全链条。潍坊全市已组建154个乡村振兴片区，覆盖1666个村庄。",
        parent_area_key="WF-154pianqu", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370076", name="环泰山文化旅游廊道（白马里）", name_norm="环泰山文化旅游廊道",
        type_code="T03", type_primary_note="泰山区泰前街道；6村7.3公里廊道；石榴+文旅",
        tags="示范带;文旅",
        province_code="370000", city_code="370900", county_code="370902", town_codes="泰前街道",
        cover_desc="泰安市泰山区白马里街区牵引，串联岱道庵、三合、上峪、水牛埠、黄山头等6村，全长7.3公里",
        scale_villages="6", scale_towns="1",
        founded_ymd="2025-01-01", founded_precision="year", status="运行中",
        lead_org="泰山区委区政府", issuer="泰安市委农办",
        summary="以白马里街区为牵引串联环山路沿线6个村落文旅资源，全长7.3公里环泰山文化旅游廊道。2025年片区村集体总收入2300余万元。",
        parent_area_key="", first_source_id="S370200", record_state="active",
        created_at="2025-01-01", updated_at="2026-09-30", created_by="SD-batch02",
    ),
    dict(
        area_id="A370077", name="黄山馆镇乡村振兴片区", name_norm="黄山馆镇乡村振兴片区",
        type_code="T04", type_primary_note="龙口市黄山馆镇；格润富德乳肉牛；6村1100户",
        tags="产业",
        province_code="370000", city_code="370600", county_code="370681", town_codes="黄山馆镇",
        cover_desc="烟台龙口市黄山馆镇，西门塔尔牛养殖+乳肉加工+田园综合体",
        scale_villages="6", scale_towns="1",
        founded_ymd="2026-09-22", founded_precision="year", status="运行中",
        lead_org="黄山馆镇党委", issuer="烟台市委农办",
        summary="黄山馆镇依托格润富德农牧科技，片区内土地、劳动力、文旅资源串联；带动全镇6个村1100多户稳定增收，创造固定岗位500多个。龙口建设市级以上片区8个、县级片区12个，辐射带动300个村。",
        parent_area_key="LK-8plus12", first_source_id="S370200", record_state="active",
        created_at="2026-09-22", updated_at="2026-09-30", created_by="SD-batch02",
    ),
]


def append_rows(path: Path, fields: list[str], rows: list[dict]) -> int:
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
            w.writerow({h: r.get(h, "") for h in fields})
        for r in added:
            w.writerow({h: r.get(h, "") for h in fields})
    return len(added)


def main() -> None:
    # raw evidence
    raw = Path(r"D:\CODEX\全国乡村片区化数据库\data\raw\SD\20260922-shandong-gedizhemeigan")
    raw.mkdir(parents=True, exist_ok=True)
    if not (raw / "meta.json").exists():
        (raw / "meta.json").write_text(
            '{\n  "url": "https://www.sdxc.gov.cn/jzyl/ztxcsy/202609/t20260922_18141933.htm",\n'
            '  "title": "片区化推进乡村振兴，山东各地这么干",\n'
            '  "publisher": "山东宣传网/大众日报",\n'
            '  "published_ymd": "2026-09-22",\n'
            '  "fetched_at": "2026-09-30T19:00:00+08:00",\n'
            '  "cred": "A",\n  "hash_sha256": ""\n}\n',
            encoding="utf-8",
        )
        (raw / "原文.md").write_text(
            "# 片区化推进乡村振兴，山东各地这么干\n\n"
            "- 发布者：山东宣传网/大众日报\n- 发布日期：2026-09-22\n"
            "- URL：https://www.sdxc.gov.cn/jzyl/ztxcsy/202609/t20260922_18141933.htm\n\n"
            "## 正文相关摘录\n\n"
            "济南建设省市县三级乡村振兴片区85个、覆盖村庄887个。"
            "商河县玉皇庙镇段家村位于“粮安商河·全域和美”片区，覆盖10个自然村。"
            "滨州建成省市县三级乡村振兴片区83个。"
            "东营规划建设20个省级、33个市级、17个县级片区，覆盖40%的村庄；汀罗片区覆盖12个村。"
            "聊城创建省、市、县三级乡村振兴片区101个；堂邑镇“邑路繁花”片区葫芦产业年产值18亿元。"
            "龙口市建设市级以上片区8个、县级片区12个，辐射带动300个村。"
            "潍坊全市已组建154个乡村振兴片区，覆盖1666个村庄。"
            "淄博桓台起凤镇打造“齐风湖韵”乡村振兴片区，统筹6个村。"
            "莒县夏庄镇组建马坡村共富茶仓“跨村联建”片区，整合6个村。"
            "诸城密州街道“文脉卢山·果韵密州”乡村振兴片区，3个社区6个网格。"
            "泰安白马里串联环山路6个村落，全长7.3公里环泰山文化旅游廊道。\n",
            encoding="utf-8",
        )

    n = append_rows(BY / "SD-area.csv", AREA_FIELDS, NEW_SD)
    n += append_rows(BY / "SD-source.csv", SRC_FIELDS, [SD_SRC])
    maps = [{"area_id": a["area_id"], "source_id": "S370200", "entity_type": "area", "rel": "primary"} for a in NEW_SD]
    n += append_rows(BY / "SD-area_source_map.csv", MAP_FIELDS, maps)
    # region map: county codes
    regs = []
    for a in NEW_SD:
        if a.get("county_code"):
            regs.append({"area_id": a["area_id"], "region_code": a["county_code"], "role": "county", "is_core": "1"})
    n += append_rows(BY / "SD-area_region_map.csv", REGMAP_FIELDS, regs)
    print(f"appended rows ~{n}")


if __name__ == "__main__":
    main()
