# -*- coding: utf-8 -*-
"""HB02 批次 7：孝昌县省级美丽乡村示范片试点县认定 1 条。"""
from scripts.legacy._hb02_lib import add, body

add(
    title="孝感两地入选全省美丽乡村示范片建设试点县（孝昌县、安陆市）",
    url="https://sthjt.hubei.gov.cn/dszxxsb/xgs/202112/t20211213_3909736.shtml",
    full_text=body("xg_shifanpian"),
    issuer="孝感市生态环境局（省生态环境厅“地方信息”栏目发布）",
    issuer_level="city", doc_type="动态", source_kind="部门动态", credibility="B",
    county_code="420921", city_code="420900", published_ymd="2021-12-13",
    summary="省生态环境厅网站发布的地方信息，是孝昌县片区/示范片建设链条最早的省级来源：经专家评审、公开答辩，孝感市孝昌县、安陆市两地被省财政厅确定为2022年度美丽乡村示范片建设试点县，全省仅11个县（市、区）入围，省级财政在政策和资金方面给予支持。文中给出湖北对“美丽乡村示范片”的官方界定——“通过美丽乡村精品村点、线、片、带、圈的衔接推进和布局优化，引导人才、土地、资金、产业、信息等优质资源聚集的片区”，并援引《湖北省美丽乡村示范片建设试点项目管理暂行办法》，规定建设周期两年、需强化绩效评价。该界定与孝昌后来获评的“牛迹仙踪·稻香共富”样板带属同一制度谱系（示范片—样板带）。",
    slug="hb-xg-xc-shifanpian-shidianxian-rending",
    instruments="财政,示范片,片区,试点县,项目管理办法,绩效评价,精品村点线片带圈,资源聚集,三生同步,产业融合",
    scope_desc="孝昌县、安陆市入选2022年度全省美丽乡村示范片建设试点县（全省11个）",
    areas=[{"area_id": "A420019", "entity_type": "area", "rel": "support"}],
    events=[{"area_id": "A420019", "entity_type": "area", "event_type": "省级试点认定", "ymd": "2021-12",
             "note": "孝昌县被省财政厅确定为2022年度美丽乡村示范片建设试点县"}],
)

print("batch7 done")
