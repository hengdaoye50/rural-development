#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SD-batch08：济南 85 / 潍坊 154 剩余具名片区入库。

只写 data/clean/by_province/SD-*.csv（追加）与已落盘的 data/raw/SD/ 快照。
不 merge、不 build、不改 master。
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY = ROOT / "data" / "clean" / "by_province"
CREATED = "SD-batch08"
STAMP = "2026-10-12"
FETCHED = "2026-10-12T13:00:00+08:00"

AREA_FIELDS = [
    "area_id", "name", "name_norm", "type_code", "type_primary_note", "tags",
    "province_code", "city_code", "county_code", "town_codes", "cover_desc",
    "scale_villages", "scale_towns", "founded_ymd", "founded_precision",
    "status", "lead_org", "issuer", "summary", "parent_area_key",
    "first_source_id", "record_state", "created_at", "updated_at", "created_by",
]
SOURCE_FIELDS = [
    "source_id", "area_id", "url", "title", "publisher", "published_ymd",
    "excerpt", "fetched_at", "credibility", "local_path", "hash_sha256",
]
MAP_FIELDS = ["area_id", "source_id", "entity_type", "rel"]
REGION_FIELDS = ["area_id", "region_code", "role", "is_core"]

AREAS = [
    dict(
        area_id="A370188", name="九龙观澜片区", name_norm="九龙观澜片区",
        type_code="T05",
        type_primary_note="钢城颜庄街道9村；农文旅深融共生；泉韵乡居金秋⑨/精品线路⑤",
        tags="农文旅;文创;研学",
        province_code="370000", city_code="370100", county_code="370117",
        town_codes="颜庄街道",
        cover_desc="钢城区西北部颜庄街道以澜头柳桥峪孙家庄为中心9个村组成九龙观澜片区构建传统文创+红色研学+康养度假+农产展销沉浸式体验集群",
        scale_villages="9", scale_towns="1", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="钢城区农业农村局/爱济南/省发改委",
        summary="泉韵乡居金秋目的地第⑨篇具名；2026-04泉韵乡居农文旅精品线路⑤静赏钢城山水清欢；孙家庄柿子树下露营地柳桥峪沿河路澜头明清古村非遗。",
        parent_area_key="", first_source_id="S370242", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370189", name="龙韵田园片区", name_norm="龙韵田园片区",
        type_code="T04",
        type_primary_note="钢城南部12村；艾山街道龙韵田园+凤梧百草园",
        tags="产业;农文旅",
        province_code="370000", city_code="370100", county_code="370117",
        town_codes="艾山街道",
        cover_desc="钢城区南部龙韵田园片区覆盖12个村与艾山街道龙韵田园凤梧百草两大产业园联动发展中草药辣椒小米等特色农业",
        scale_villages="12", scale_towns="1", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="钢城区委区政府/省发改委",
        summary="钢城四线布局北部花开辛庄28村东部汶水桃源9村南部龙韵田园12村西部九龙观澜；2026-07财政局稿已建成5个示范片区实现街道全覆盖；计划2030建成10个。",
        parent_area_key="", first_source_id="S370243", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370190", name="和美里辛片区", name_norm="和美里辛片区",
        type_code="T01",
        type_primary_note="钢城里辛街道；片区创建加快推进中",
        tags="和美乡村",
        province_code="370000", city_code="370100", county_code="370117",
        town_codes="里辛街道",
        cover_desc="钢城区和美里辛乡村振兴片区与龙韵田园等2个片区加快推进2026年实现片区创建街道全覆盖",
        scale_villages="", scale_towns="", founded_ymd="", founded_precision="unknown",
        status="待核", lead_org="", issuer="钢城区政府/舜网/省会新观察",
        summary="2026-01钢城区政府工作报告点名和美里辛片区加快推进；2026-07-06稿仍写加快推进而2026-07-31财政局稿已建成5个片区实现街道全覆盖是否含里辛待核。",
        parent_area_key="", first_source_id="S370243", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370191", name="瓜香蔬韵·和美稻田片区", name_norm="瓜香蔬韵和美稻田片区",
        type_code="T04",
        type_primary_note="寿光稻田镇中西部6村；智慧农业+三产联动",
        tags="产业;和美乡村",
        province_code="370000", city_code="370700", county_code="370783",
        town_codes="稻田镇",
        cover_desc="寿光市稻田镇中西部瓜香蔬韵和美稻田乡村振兴片区覆盖崔岭西村西稻田村崔岭东村阁后王村梁武赵村潘家村6个行政村共2087户8095人",
        scale_villages="6", scale_towns="1", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="寿光市稻田镇/齐鲁晚报·齐鲁壹点",
        summary="总投资1.9亿元建1500亩地上棚示范园区；海而思数字种苗中心年出苗6000万株；众旺果蔬合作社GAP双认证冬奥直供+粤港澳菜篮子；桂河芹菜崔西一品玉指黄瓜等品牌。",
        parent_area_key="", first_source_id="S370245", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370192", name="清馨云华·茶乡桃林片区", name_norm="清馨云华茶乡桃林片区",
        type_code="T05",
        type_primary_note="诸城桃林镇；连片茶园+茶旅融合",
        tags="农文旅;产业",
        province_code="370000", city_code="370700", county_code="370782",
        town_codes="桃林镇",
        cover_desc="诸城市桃林镇清馨云华茶乡桃林乡村振兴片区依托连片茶园铺开茶旅融合路径",
        scale_villages="", scale_towns="", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="潍坊日报/齐鲁网",
        summary="诸城片区化典型之一与食兴栗乡产融昌城龙山古脉药都新韵并列点名；桃林镇为诸城绿茶主产区。",
        parent_area_key="", first_source_id="S370244", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370193", name="龙山古脉·药都新韵片区", name_norm="龙山古脉药都新韵片区",
        type_code="T04",
        type_primary_note="诸城百尺河镇；中草药白花丹参",
        tags="产业",
        province_code="370000", city_code="370700", county_code="370782",
        town_codes="百尺河镇",
        cover_desc="诸城市百尺河镇龙山古脉药都新韵乡村振兴片区深耕中草药产业白花丹参获评省级道地药材生产基地",
        scale_villages="", scale_towns="", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="潍坊日报/齐鲁网",
        summary="诸城片区化典型之一；白花丹参省级道地药材生产基地。",
        parent_area_key="", first_source_id="S370244", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370194", name="万亩枣园·十里画卷片区", name_norm="万亩枣园十里画卷片区",
        type_code="T04",
        type_primary_note="昌邑；梨枣/蜜罐枣；全国最大梨枣基地",
        tags="产业",
        province_code="370000", city_code="370700", county_code="370786",
        town_codes="",
        cover_desc="昌邑市万亩枣园十里画卷乡村振兴片区创新片区+共富公司+合作社+农户共建共享机制联合省农科院攻关蜜罐枣等新品种开发枣芽茶枣泥面食等深加工产品年销售收入突破3000万元",
        scale_villages="", scale_towns="", founded_ymd="", founded_precision="unknown",
        status="运行中", lead_org="", issuer="潍坊日报/齐鲁网",
        summary="建成全国最大的梨枣生产基地价格形成中心和交易中心；带动农民人均收入达5万元。",
        parent_area_key="", first_source_id="S370244", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
    dict(
        area_id="A370195", name="胶东云廊共富片区", name_norm="胶东云廊共富片区",
        type_code="T05",
        type_primary_note="高密；胶河东村张鲁村；黑陶非遗田园",
        tags="农文旅;产业",
        province_code="370000", city_code="370700", county_code="370785",
        town_codes="",
        cover_desc="高密市胶东云廊共富片区通过党建工作协调委员会搭建联村议事平台落地黑陶非遗田园等特色项目培育有机农业等多元业态带动胶河东村张鲁村协同运营利益共享",
        scale_villages="2", scale_towns="", founded_ymd="", founded_precision="unknown",
        status="待核", lead_org="", issuer="潍坊日报/齐鲁网",
        summary="高密围绕潍水东岸胶河两岸G20沿线三大战略组团把3至7个村组建共富联合体15个共富片区有序起势；胶东云廊为其中之一具名。",
        parent_area_key="", first_source_id="S370244", record_state="active",
        created_at=STAMP, updated_at=STAMP, created_by=CREATED,
    ),
]

SOURCES = [
    dict(
        source_id="S370242", area_id="A370188",
        url="https://www.sohu.com/a/1079966600_121106991",
        title="济南泉韵乡居金秋目的地趣游乡村指南系列（含⑨九龙观澜）",
        publisher="济南市农业农村局/爱济南/大众新闻",
        published_ymd="2026-09-23",
        excerpt="济南市农业农村局联合省市媒体推出泉韵乡居金秋目的地趣游乡村指南专题。系列⑨走进钢城区九龙观澜片区；系列⑤为历城恬居云台；系列⑥为莱芜雪野水乡和美画廊（与雪野三乡和美画廊疑同体）。钢城九龙观澜以农文旅深融共生为主轴构建传统文创+红色研学+康养度假+农产展销集群；颜庄街道以澜头柳桥峪孙家庄为中心9个村组成。",
        fetched_at="2026-10-12T13:00:00+08:00", credibility="B",
        local_path="data/raw/SD/20261012-jinan-jinqiu-jiulongguanlan/原文.md",
        hash_sha256="",
    ),
    dict(
        source_id="S370243", area_id="A370189",
        url="http://www.gangcheng.gov.cn/gongkai/site_gangchengquqczjh/channel_6389b595375991828264ee1a/doc_6a71a954a0d5d178e3831490.html",
        title="钢城区片区化布局：花开辛庄/九龙观澜/汶水桃源/龙韵田园/和美里辛",
        publisher="钢城区财政局/新华网山东/舜网",
        published_ymd="2026-07-31",
        excerpt="钢城区已建成龙韵田园九龙观澜汶水桃源花开辛庄等5个乡村振兴示范片区实现街道全覆盖。区位布局北部花开辛庄28个村东部汶水桃源9个村南部龙韵田园12个村西部九龙观澜（颜庄9村）。2026-01稿另载龙韵田园和美里辛2个片区加快推进。计划到2030年建成10个片区辐射覆盖村庄达60%。",
        fetched_at="2026-10-12T13:05:00+08:00", credibility="A",
        local_path="data/raw/SD/20261012-gangcheng-5pianqu/原文.md",
        hash_sha256="",
    ),
    dict(
        source_id="S370244", area_id="A370192",
        url="https://weifang.iqilu.com/wfyaowen/2026/0824/5938412.shtml",
        title="片区组团绘就锦绣田园：潍坊片区化推进乡村振兴",
        publisher="潍坊日报/齐鲁网",
        published_ymd="2026-08-24",
        excerpt="潍坊已组建154个乡村振兴片区覆盖1666个村庄。诸城桃林镇清馨云华茶乡桃林片区茶旅融合；百尺河镇龙山古脉药都新韵片区白花丹参省级道地药材基地；昌邑万亩枣园十里画卷片区蜜罐枣枣芽茶年销售3000万元全国最大梨枣基地；高密胶东云廊共富片区黑陶非遗田园带动胶河东村张鲁村；潍城于河印象片区统筹9村3公里农文旅环线年接待游客150万人次（全称上农智田于河印象）。",
        fetched_at="2026-10-12T13:10:00+08:00", credibility="A",
        local_path="data/raw/SD/20261012-weifang-zutuan-jinxiu/原文.md",
        hash_sha256="",
    ),
    dict(
        source_id="S370245", area_id="A370191",
        url="https://m.sohu.com/a/1079036411_121218495",
        title="科技赋农三产联动潍坊寿光书写乡村振兴新答卷（瓜香蔬韵和美稻田）",
        publisher="齐鲁晚报·齐鲁壹点",
        published_ymd="2026-09-21",
        excerpt="寿光市稻田镇中西部瓜香蔬韵和美稻田乡村振兴片区覆盖崔岭西村西稻田村崔岭东村阁后王村梁武赵村潘家村6个行政村共2087户8095人。总投资1.9亿元建设1500亩地上棚示范园区；海而思数字种苗中心国内首创80mm纸钵大苗技术年出苗6000万株；众旺果蔬合作社中国与全球GAP双认证冬奥蔬菜直供基地。",
        fetched_at="2026-10-12T13:15:00+08:00", credibility="B",
        local_path="data/raw/SD/20261012-shouguang-guaxiangshuyun/原文.md",
        hash_sha256="",
    ),
]

# 一文多片区 + 旧条目补强
MAPS = [
    ("A370188", "S370242", "area", "primary"),
    ("A370188", "S370243", "area", "support"),
    ("A370189", "S370243", "area", "primary"),
    ("A370190", "S370243", "area", "primary"),
    ("A370191", "S370245", "area", "primary"),
    ("A370192", "S370244", "area", "primary"),
    ("A370193", "S370244", "area", "primary"),
    ("A370194", "S370244", "area", "primary"),
    ("A370195", "S370244", "area", "primary"),
    ("A370023", "S370244", "area", "support"),  # 上农智田·于河印象全名+9村
    ("A370079", "S370242", "area", "support"),  # 雪野水乡异名线索
    ("A370084", "S370243", "area", "support"),  # 花开辛庄28村
    ("A370143", "S370243", "area", "support"),  # 汶水桃源9-10村全口径
]

REGIONS = [
    ("A370188", "370117", "county", "1"),
    ("A370189", "370117", "county", "1"),
    ("A370190", "370117", "county", "1"),
    ("A370191", "370783", "county", "1"),
    ("A370192", "370782", "county", "1"),
    ("A370193", "370782", "county", "1"),
    ("A370194", "370786", "county", "1"),
    ("A370195", "370785", "county", "1"),
]


def append_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    exists = path.exists() and path.stat().st_size > 0
    # 幂等：已存在的 area_id/source_id 跳过
    seen: set[str] = set()
    if exists:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                key = r.get(fieldnames[0], "")
                if key:
                    seen.add(key)
        # map 表用复合键
    mode = "a" if exists else "w"
    with path.open(mode, encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        if not exists:
            w.writeheader()
        for row in rows:
            k = row[fieldnames[0]]
            if fieldnames == MAP_FIELDS:
                k = f"{row['area_id']}|{row['source_id']}|{row['rel']}"
            if k in seen:
                continue
            w.writerow(row)
            seen.add(k)


def append_map(path: Path, rows: list[tuple]) -> None:
    exists = path.exists() and path.stat().st_size > 0
    seen: set[str] = set()
    if exists:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                seen.add(f"{r['area_id']}|{r['source_id']}|{r['rel']}")
    mode = "a" if exists else "w"
    with path.open(mode, encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MAP_FIELDS, lineterminator="\n")
        if not exists:
            w.writeheader()
        for area_id, source_id, et, rel in rows:
            k = f"{area_id}|{source_id}|{rel}"
            if k in seen:
                continue
            w.writerow(dict(area_id=area_id, source_id=source_id, entity_type=et, rel=rel))
            seen.add(k)


def append_region(path: Path, rows: list[tuple]) -> None:
    exists = path.exists() and path.stat().st_size > 0
    seen: set[str] = set()
    if exists:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                seen.add(f"{r['area_id']}|{r['region_code']}")
    mode = "a" if exists else "w"
    with path.open(mode, encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REGION_FIELDS, lineterminator="\n")
        if not exists:
            w.writeheader()
        for area_id, code, role, core in rows:
            k = f"{area_id}|{code}"
            if k in seen:
                continue
            w.writerow(dict(area_id=area_id, region_code=code, role=role, is_core=core))
            seen.add(k)


def main() -> None:
    append_csv(BY / "SD-area.csv", AREA_FIELDS, AREAS)
    append_csv(BY / "SD-source.csv", SOURCE_FIELDS, SOURCES)
    append_map(BY / "SD-area_source_map.csv", MAPS)
    append_region(BY / "SD-area_region_map.csv", REGIONS)
    print(f"areas+{len(AREAS)} sources+{len(SOURCES)} maps+{len(MAPS)} regions+{len(REGIONS)}")


if __name__ == "__main__":
    main()
