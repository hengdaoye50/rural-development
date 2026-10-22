"""One-shot: write Tibet raw evidence + clean by_province CSVs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"D:\CODEX\全国乡村片区化数据库")
RAW = ROOT / "data" / "raw" / "XZ"
BY = ROOT / "data" / "clean" / "by_province"
RAW.mkdir(parents=True, exist_ok=True)


def save_raw(slug, url, title, publisher, published_ymd, excerpt, cred, body):
    d = RAW / slug
    d.mkdir(parents=True, exist_ok=True)
    meta = {
        "url": url,
        "title": title,
        "publisher": publisher,
        "published_ymd": published_ymd,
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "cred": cred,
        "hash_sha256": "",
    }
    (d / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = (
        f"# {title}\n\n"
        f"- 发布者：{publisher}\n"
        f"- 发布日期：{published_ymd}\n"
        f"- URL：{url}\n\n"
        f"## 正文相关摘录\n\n{body}\n"
    )
    (d / "原文.md").write_text(md, encoding="utf-8")


save_raw(
    "20231010-zhufeng-liancun-dangwei",
    "https://www.xizang.gov.cn/xwzx_406/qxxw/202310/t20231010_380000.html",
    "日喀则定日县珠峰“联村党委”推动联建村抱团发展联合振兴",
    "西藏日报/西藏自治区人民政府网",
    "2023-10-10",
    "定日县整合扎西宗乡村级党组织、边境派出所党组织和临时党支部，于今年5月成立中共珠峰联村委员会，推动联建村抱团发展、联合振兴。",
    "A",
    "定日县整合扎西宗乡村级党组织、边境派出所党组织和临时党支部，于今年5月成立中共珠峰联村委员会，推动联建村抱团发展、联合振兴。\n\n"
    "定日县划拨专项经费43万余元，实行行政管理区域、村民自治主体、集体资产资源权属不变，到村各类扶持资金、项目、政策等投向和受益范围不变，"
    "到村转移支付资金、运转经费和领取生活补贴人员补贴政策等拨付标准、渠道不变；保持联建村财务管理账目独立、核算独立、收支独立；"
    "做到乡村振兴各类规划统一、工作部署统一、工作落实统一，形成联建村同规划、同议事、同分享工作机制。\n\n"
    "据了解，珠峰“联村党委”争取各方支持，为景区沿线酒店（民宿）吸引投资近2000万元；出租门面79个，收入930余万元，新增就业群众78名。"
    "大力发展民宿酒店经济，珠峰大本营59顶经营性帐篷创收1450余万元，为群众分红400余万元；吸引沃玛龙自然村群众建成农家体验馆4家。",
)

save_raw(
    "20251223-dingri-liancun-gongjian",
    "https://www.rkzzfdj.gov.cn/staticPage/jcdj/nmqzxdt/20251223/238778889.html",
    "定日县：党建引领联村共建 绘就乡村振兴新画卷",
    "中共定日县委组织部/日喀则珠峰党建",
    "2025-12-23",
    "2023年5月，率先在扎西宗镇整合7个村级党组织、2个边境派出所党支部、1个富民公司党支部和1个珠峰大本营临时党支部，成立中共珠峰联村党委。"
    "随后推广跨村联建模式，同步组建协格尔镇甲谐联村党委，推动发展模式从“小支部单打独斗”向“大党委协同作战”转变。",
    "A",
    "2023年5月，率先在扎西宗镇整合7个村级党组织、2个边境派出所党支部、1个富民公司党支部和1个珠峰大本营临时党支部，成立中共珠峰联村党委。"
    "随后推广跨村联建模式，同步组建协格尔镇甲谐联村党委，推动发展模式从“小支部单打独斗”向“大党委协同作战”转变。"
    "自成立以来，两个联村党委领办的公司累计创收5386.84万元，带动灵活就业2300余人次，解决固定就业129人。\n\n"
    "按照“地域相邻、村情相似、产业相近”原则，组建两个区域化联村党委……选派乡镇党委副书记兼任联村党委书记。"
    "珠峰联村党委领办公司，围绕特色产品销售、租赁经营、劳务合作、帐篷营地、餐饮洗涤等拓展产业。"
    "甲谐联村党委依托县城优势，发展德克士餐饮、糌粑加工、洗车场、商贸批发等项目，采取“联村党委+公司+村集体经济”模式推动多元化发展。",
)

save_raw(
    "20250925-gongjue-awang-pianqu",
    "https://nynct.xizang.gov.cn/xwzx/xzsn/202509/t20250925_501501.html",
    "党建领航产业兴 文化铸魂根基稳——昌都市贡觉县党建引领乡村振兴综述",
    "西藏自治区农业农村厅",
    "2025-09-25",
    "2023年，阿旺乡整合9个村的集体经济项目，强乡兴村投入600万元村资金，组建加措忠畜牧养殖专业合作社，"
    "创新构建“阿旺片区1－9村党支部＋合作社＋牧户”的集体经济发展模式。",
    "A",
    "2023年，阿旺乡整合9个村的集体经济项目，强乡兴村投入600万元村资金，组建加措忠畜牧养殖专业合作社，"
    "创新构建“阿旺片区1－9村党支部＋合作社＋牧户”的集体经济发展模式。\n\n"
    "2024年，随着昌都市智慧牧业平台投入使用，每只羊都戴上了标识信息牌……阿旺乡草场归集体所有，"
    "合作社制定了合理的收益分配方案：70％用于群众分红，5％作为村集体经济带头人奖励资金，"
    "20％留作下一年度集体经济运转资金，5％作为村党组织服务群众经费。"
    "2024年，阿旺乡村集体经济收入达216万余元，平均每户分红约3100元。",
)

save_raw(
    "20240625-nierong-liancun-dangwei",
    "https://www.linzhi.gov.cn/xwzx_406/qxxw/202406/t20240625_422575.html",
    "按下和美乡村建设“加速键”——聂荣县探索乡村振兴“特色路径”扫描",
    "西藏日报/西藏自治区人民政府网",
    "2024-06-25",
    "聂荣县在全市率先开展“联村党委”试点工作，挂牌成立联村党委29个，实现资源共享、风险共担、抱团取暖，"
    "形成“党建引领、片区发展、融合互动、全域推进”的态势。",
    "B",
    "为提升基层党组织政治引领力、党群凝聚力、队伍战斗力、发展推动力、示范带动力，"
    "聂荣县在全市率先开展“联村党委”试点工作，挂牌成立联村党委29个，实现资源共享、风险共担、抱团取暖，"
    "形成“党建引领、片区发展、融合互动、全域推进”的态势，进一步健全组织体系、优化组织功能、加强组织担当、提升组织效能。",
)

save_raw(
    "20260706-gaoyuan-hemei-pianquhua-shidian",
    "https://nynct.xizang.gov.cn/xwzx/tpxw/202607/t20260706_548815.html",
    "权威发布丨我区“十四五”农业农村发展成果丰硕",
    "西藏自治区农业农村厅/西藏发布",
    "2026-07-06",
    "“十五五”时期……同时，启动实施高原和美乡村片区化试点建设。",
    "A",
    "学习运用“千万工程”经验，累计建设高原和美村庄1000个……启动实施高原和美乡村片区化试点建设。"
    "……在具体建设村庄选择上，优先选择公路沿线、边境一线和城镇周边地区、旅游风景区、重点产业集聚区“两线三区”的村庄，"
    "同时适度考量农牧民房屋与基础设施的协调性，对常住人口较多、村庄规划已编制审批、产业基础好、基础设施短板明显、"
    "基层组织完备、未来将长久存续的集聚提升类行政村重点支持。截至目前，2026年实施的200个高原和美乡村已开工175个，完工2个。",
)

save_raw(
    "20250924-mozhugongka-pianquhua-zutuan",
    "https://www.lasa.gov.cn/lasa/c100891/202509/643ec4b483b74cc2a51d3b342b5b0abd.shtml",
    "墨竹工卡县推进乡村建设示范见成效 绘就宜居宜业和美乡村新图景",
    "西藏日报/拉萨市人民政府网",
    "2025-09-24",
    "探索联村共建、片区化组团发展新路径，项目推进中严格把控施工质量关、竣工验收关，"
    "力求实现人居环境连片整治、基础设施互联互通、资源优势互补、产业融合提升、和美共富组团发展的目标。",
    "B",
    "墨竹工卡县农业农村局相关负责人表示，墨竹工卡县始终把群众的意愿放在首位……"
    "探索联村共建、片区化组团发展新路径，项目推进中严格把控施工质量关、竣工验收关，"
    "力求实现人居环境连片整治、基础设施互联互通、资源优势互补、产业融合提升、和美共富组团发展的目标，"
    "让农牧民群众真正享受到发展红利。据介绍，截至目前，墨竹工卡县已创建美丽宜居和美乡村建设示范村20个。",
)

print("raw ok")

# region
reg_path = ROOT / "data" / "clean" / "region.csv"
with open(reg_path, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
existing = {r[0] for r in rows[1:] if r}
adds = [
    ["540200", "日喀则市", "日喀则", "city", "540000", ""],
    ["540223", "定日县", "定日", "county", "540200", ""],
    ["540300", "昌都市", "昌都", "city", "540000", ""],
    ["540322", "贡觉县", "贡觉", "county", "540300", ""],
    ["540600", "那曲市", "那曲", "city", "540000", ""],
    ["540623", "聂荣县", "聂荣", "county", "540600", ""],
]
added = [a[0] for a in adds if a[0] not in existing]
rows.extend(a for a in adds if a[0] not in existing)
with open(reg_path, "w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(rows)
print("region ok, added", added)

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
BELT_FIELDS = [
    "belt_id", "name", "name_norm", "belt_type", "theme", "province_code",
    "city_code", "county_code", "cover_desc", "scale_villages", "scale_towns",
    "announced_ymd", "year_precision", "issuer", "source_id", "summary",
    "institutional_note", "record_state", "created_at", "updated_at", "created_by",
]
BELTREG_FIELDS = ["belt_id", "region_code", "role", "is_core"]

areas = [
    {
        "area_id": "A540001",
        "name": "珠峰联村党委",
        "name_norm": "珠峰联村党委",
        "type_code": "T02",
        "type_primary_note": "扎西宗镇跨村联建党组织；整合7个村级党组织+边境派出所+公司+临时党支部",
        "tags": "党建;联村共建;文旅",
        "province_code": "540000",
        "city_code": "540200",
        "county_code": "540223",
        "town_codes": "扎西宗镇",
        "cover_desc": "定日县扎西宗镇联建单元：7个村级党组织、2个边境派出所党支部、1个富民公司党支部、1个珠峰大本营临时党支部",
        "scale_villages": "7",
        "scale_towns": "1",
        "founded_ymd": "2023-05-01",
        "founded_precision": "month",
        "status": "运行中",
        "lead_org": "珠峰联村党委（扎西宗镇党委副书记兼党委书记）",
        "issuer": "中共定日县委",
        "summary": "2023年5月成立中共珠峰联村委员会，推行联村共建，领办公司经营帐篷营地、民宿等，大本营59顶帐篷创收1450余万元、分红400余万元。",
        "parent_area_key": "",
        "first_source_id": "S540001",
        "record_state": "active",
        "created_at": "2023-05-01",
        "updated_at": "2026-09-30",
        "created_by": "XZ-batch01",
    },
    {
        "area_id": "A540002",
        "name": "甲谐联村党委",
        "name_norm": "甲谐联村党委",
        "type_code": "T02",
        "type_primary_note": "协格尔镇跨村联建党组织；珠峰联村党委推广组建",
        "tags": "党建;联村共建;产业",
        "province_code": "540000",
        "city_code": "540200",
        "county_code": "540223",
        "town_codes": "协格尔镇",
        "cover_desc": "定日县协格尔镇联建单元，依托县城优势发展餐饮、糌粑加工、商贸等",
        "scale_villages": "",
        "scale_towns": "1",
        "founded_ymd": "2023-01-01",
        "founded_precision": "year",
        "status": "运行中",
        "lead_org": "甲谐联村党委",
        "issuer": "中共定日县委",
        "summary": "在珠峰联村党委之后同步组建，采取“联村党委+公司+村集体经济”模式，发展德克士餐饮、糌粑加工、洗车场、商贸批发等项目。",
        "parent_area_key": "DR-liancun",
        "first_source_id": "S540002",
        "record_state": "active",
        "created_at": "2023-01-01",
        "updated_at": "2026-09-30",
        "created_by": "XZ-batch01",
    },
    {
        "area_id": "A540003",
        "name": "阿旺片区",
        "name_norm": "阿旺片区",
        "type_code": "T02",
        "type_primary_note": "阿旺片区1－9村党支部＋合作社＋牧户；跨村产业联合",
        "tags": "党建;产业",
        "province_code": "540000",
        "city_code": "540300",
        "county_code": "540322",
        "town_codes": "阿旺乡",
        "cover_desc": "贡觉县阿旺乡1－9村联建单元，加措忠畜牧养殖专业合作社",
        "scale_villages": "9",
        "scale_towns": "1",
        "founded_ymd": "2023-01-01",
        "founded_precision": "year",
        "status": "运行中",
        "lead_org": "阿旺片区党支部＋合作社",
        "issuer": "贡觉县委县政府",
        "summary": "2023年阿旺乡整合9个村集体经济项目，投入600万元组建加措忠畜牧养殖专业合作社，构建“阿旺片区1－9村党支部＋合作社＋牧户”模式；2024年村集体收入216万余元。",
        "parent_area_key": "",
        "first_source_id": "S540003",
        "record_state": "active",
        "created_at": "2023-01-01",
        "updated_at": "2026-09-30",
        "created_by": "XZ-batch01",
    },
    {
        "area_id": "A540004",
        "name": "聂荣县联村党委（试点）",
        "name_norm": "聂荣县联村党委",
        "type_code": "T02",
        "type_primary_note": "全县挂牌联村党委29个；单体名称未公开，聚合记录待拆分",
        "tags": "党建;联村共建",
        "province_code": "540000",
        "city_code": "540600",
        "county_code": "540623",
        "town_codes": "",
        "cover_desc": "那曲市聂荣县联村党委试点，全县挂牌29个联村党委（来源未逐一点名）",
        "scale_villages": "",
        "scale_towns": "",
        "founded_ymd": "2024-01-01",
        "founded_precision": "year",
        "status": "待核",
        "lead_org": "聂荣县委组织部",
        "issuer": "聂荣县委县政府",
        "summary": "2024年报道：聂荣县在那曲市率先开展联村党委试点，挂牌成立联村党委29个，形成“党建引领、片区发展、融合互动、全域推进”态势。单体名称未见公开清单，暂作聚合记录。",
        "parent_area_key": "",
        "first_source_id": "S540004",
        "record_state": "active",
        "created_at": "2024-01-01",
        "updated_at": "2026-09-30",
        "created_by": "XZ-batch01",
    },
]

sources = [
    {
        "source_id": "S540001",
        "area_id": "A540001",
        "url": "https://www.xizang.gov.cn/xwzx_406/qxxw/202310/t20231010_380000.html",
        "title": "日喀则定日县珠峰“联村党委”推动联建村抱团发展联合振兴",
        "publisher": "西藏日报/西藏自治区人民政府网",
        "published_ymd": "2023-10-10",
        "excerpt": "定日县整合扎西宗乡村级党组织、边境派出所党组织和临时党支部，于今年5月成立中共珠峰联村委员会，推动联建村抱团发展、联合振兴。",
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "credibility": "A",
        "local_path": "data/raw/XZ/20231010-zhufeng-liancun-dangwei/原文.md",
        "hash_sha256": "",
    },
    {
        "source_id": "S540002",
        "area_id": "A540001",
        "url": "https://www.rkzzfdj.gov.cn/staticPage/jcdj/nmqzxdt/20251223/238778889.html",
        "title": "定日县：党建引领联村共建 绘就乡村振兴新画卷",
        "publisher": "中共定日县委组织部/日喀则珠峰党建",
        "published_ymd": "2025-12-23",
        "excerpt": "2023年5月，率先在扎西宗镇整合7个村级党组织、2个边境派出所党支部、1个富民公司党支部和1个珠峰大本营临时党支部，成立中共珠峰联村党委。随后推广跨村联建模式，同步组建协格尔镇甲谐联村党委。",
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "credibility": "A",
        "local_path": "data/raw/XZ/20251223-dingri-liancun-gongjian/原文.md",
        "hash_sha256": "",
    },
    {
        "source_id": "S540003",
        "area_id": "A540003",
        "url": "https://nynct.xizang.gov.cn/xwzx/xzsn/202509/t20250925_501501.html",
        "title": "党建领航产业兴 文化铸魂根基稳——昌都市贡觉县党建引领乡村振兴综述",
        "publisher": "西藏自治区农业农村厅",
        "published_ymd": "2025-09-25",
        "excerpt": "2023年，阿旺乡整合9个村的集体经济项目，强乡兴村投入600万元村资金，组建加措忠畜牧养殖专业合作社，创新构建“阿旺片区1－9村党支部＋合作社＋牧户”的集体经济发展模式。",
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "credibility": "A",
        "local_path": "data/raw/XZ/20250925-gongjue-awang-pianqu/原文.md",
        "hash_sha256": "",
    },
    {
        "source_id": "S540004",
        "area_id": "A540004",
        "url": "https://www.linzhi.gov.cn/xwzx_406/qxxw/202406/t20240625_422575.html",
        "title": "按下和美乡村建设“加速键”——聂荣县探索乡村振兴“特色路径”扫描",
        "publisher": "西藏日报/西藏自治区人民政府网",
        "published_ymd": "2024-06-25",
        "excerpt": "聂荣县在全市率先开展“联村党委”试点工作，挂牌成立联村党委29个，实现资源共享、风险共担、抱团取暖，形成“党建引领、片区发展、融合互动、全域推进”的态势。",
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "credibility": "B",
        "local_path": "data/raw/XZ/20240625-nierong-liancun-dangwei/原文.md",
        "hash_sha256": "",
    },
    {
        "source_id": "S540005",
        "area_id": "B540001",
        "url": "https://nynct.xizang.gov.cn/xwzx/tpxw/202607/t20260706_548815.html",
        "title": "权威发布丨我区“十四五”农业农村发展成果丰硕",
        "publisher": "西藏自治区农业农村厅/西藏发布",
        "published_ymd": "2026-07-06",
        "excerpt": "启动实施高原和美乡村片区化试点建设。在具体建设村庄选择上，优先选择公路沿线、边境一线和城镇周边地区、旅游风景区、重点产业集聚区“两线三区”的村庄。",
        "fetched_at": "2026-09-30T18:00:00+08:00",
        "credibility": "A",
        "local_path": "data/raw/XZ/20260706-gaoyuan-hemei-pianquhua-shidian/原文.md",
        "hash_sha256": "",
    },
]

maps = [
    ("A540001", "S540001", "area", "primary"),
    ("A540001", "S540002", "area", "support"),
    ("A540002", "S540002", "area", "primary"),
    ("A540003", "S540003", "area", "primary"),
    ("A540004", "S540004", "area", "primary"),
    ("B540001", "S540005", "belt", "primary"),
]

regmaps = [
    ("A540001", "540223", "county", "1"),
    ("A540002", "540223", "county", "1"),
    ("A540003", "540322", "county", "1"),
    ("A540004", "540623", "county", "1"),
]

belts = [
    {
        "belt_id": "B540001",
        "name": "高原和美乡村片区化试点",
        "name_norm": "高原和美乡村片区化试点",
        "belt_type": "其他",
        "theme": "和美乡村",
        "province_code": "540000",
        "city_code": "540000",
        "county_code": "",
        "cover_desc": "自治区层面启动高原和美乡村片区化试点建设；具体县域以下点位尚未公开命名",
        "scale_villages": "",
        "scale_towns": "",
        "announced_ymd": "2026",
        "year_precision": "year",
        "issuer": "西藏自治区农业农村厅",
        "source_id": "S540005",
        "summary": "“十五五”期间启动实施高原和美乡村片区化试点建设，优先布局“两线三区”村庄。",
        "institutional_note": "省级试点表述，暂无公开的县以下命名单元，记belt；待点位公开后视机制改area。",
        "record_state": "active",
        "created_at": "2026-07-06",
        "updated_at": "2026-09-30",
        "created_by": "XZ-batch01",
    }
]

beltregs = [("B540001", "540000", "county", "1")]


def write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            if isinstance(r, dict):
                w.writerow({k: r.get(k, "") for k in fields})
            else:
                w.writerow(dict(zip(fields, r)))


write_csv(BY / "XZ-area.csv", AREA_FIELDS, areas)
write_csv(BY / "XZ-source.csv", SRC_FIELDS, sources)
write_csv(BY / "XZ-area_source_map.csv", MAP_FIELDS, maps)
write_csv(BY / "XZ-area_region_map.csv", REGMAP_FIELDS, regmaps)
write_csv(BY / "XZ-belt.csv", BELT_FIELDS, belts)
write_csv(BY / "XZ-belt_region_map.csv", BELTREG_FIELDS, beltregs)
print("clean ok", len(areas), "areas,", len(sources), "sources, 1 belt")
