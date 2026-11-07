# -*- coding: utf-8 -*-
"""HB02 批次 4：鄂城区（四峰山样板带）4 条。"""
from scripts.legacy._hb02_lib import add, body

EC = "420704"
EZC = "420700"
A = "A420018"

add(
    title="[鄂州]全省首批宜居宜业和美乡村样板带 鄂城区四峰山入选",
    url="http://nyt.hubei.gov.cn/bmdt/yw/szdt/202505/t20250521_5656794_slh.shtml",
    full_text=body("ad6c1175fd"),
    issuer="鄂州市农业农村局（省农业农村厅“市州动态”转载鄂州日报）",
    issuer_level="city", doc_type="动态", source_kind="部门动态", credibility="B",
    county_code=EC, city_code=EZC, published_ymd="2025-05-21",
    summary="省农业农村厅“市州动态”栏目转载的鄂州报道，逐项交代四峰山样板带的空间范围与资金机制：样板带位于鄂州东南部，东接黄石东方山、西连碧石白雉山、南邻黄石铁山区，北跨汀祖镇辖内刘云、华伍、岳石洪等8个行政村；背靠鄂州第一高峰四峰山、坐拥全市最大人工湖石桥水库，森林覆盖率39.8%；以“春赏花、夏避暑、秋品果、冬养生”为特色。机制上明确“汀祖镇以全域国土综合整治为抓手，整合湖北省和美乡村示范片建设资金，统筹推进人居环境整治与基础设施建设”，即样板带的建设底座是省级和美乡村示范片。末段引市农业农村局表态，提出挖掘四峰山片区红色文化、民俗非遗资源。",
    slug="hb-ez-ec-sifengshan-yangbandai-ruxuan",
    instruments="样板带,示范片,全域国土综合整治,和美乡村示范片建设资金,人居环境,基础设施,农文旅融合,千万工程,党建加产业加生态,片区,森林康养",
    scope_desc="汀祖镇刘云、华伍、岳石洪等8个行政村，森林覆盖率39.8%",
    areas=[{"area_id": A, "entity_type": "area", "rel": "primary"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "省级样板带入选", "ymd": "2025-04-28",
             "note": "入选湖北省第一批20条宜居宜业和美乡村样板带"}],
)

add(
    title="鄂州市农业农村局2025年度工作总结及2026年工作计划",
    url="https://nyj.ezhou.gov.cn/xxgk/fdzdgknr/ghxx/202602/t20260211_750663.html",
    full_text=body("43bc337cc1"),
    issuer="鄂州市农业农村局", issuer_level="city", doc_type="总结", source_kind="部门动态",
    credibility="B", county_code=EC, city_code=EZC, published_ymd="2026-02-11",
    summary="鄂州市农业农村局年度工作总结与计划，将“鄂城区四峰山‘天然氧吧·赏花品果’样板带成功入选全省第一批20条宜居宜业和美乡村样板带名单”列为市级年度成效，同段并列“长港镇峒山村获农业农村部美丽休闲乡村推介”“长港镇峒山村家风家训故事入选农业农村部《村庄里的家风家训故事》（全省仅6村）”以及全市改造农村卫生厕所12.4万座等口径。是四峰山样板带获省级认定的市级书面确认，也是鄂州市域和美乡村建设的总量底稿。",
    slug="hb-ez-nongyeju-2025-zongjie-2026-jihua",
    instruments="样板带,和美乡村,美丽休闲乡村,农村改厕,人居环境,乡村振兴,千万工程",
    scope_desc="全市年度工作；确认鄂城区四峰山样板带入选全省首批20条名单",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "年度总结确认", "ymd": "2026-02-11",
             "note": "市级年度工作总结将样板带入选列为成效"}],
)

add(
    title="【新闻发布会】解读鄂城区“三新三强”打擂台、厚筑全市“压舱石”2024年行动计划（涉和美乡村示范带部分）",
    url="https://www.echeng.gov.cn/ecqxxgk/zcjdzsk/zxjd/202404/t20240409_621200.html",
    full_text=body("echeng_sanxin"),
    issuer="鄂城区人民政府（市政府新闻发布会，信息来源鄂州融媒）",
    issuer_level="county", doc_type="其他", source_kind="新闻发布", credibility="B",
    county_code=EC, city_code=EZC, issued_ymd="2024-03-29", published_ymd="2024-04-09",
    summary="鄂城区2024年行动计划新闻发布会的官方解读稿。县域空间战略表述为“两带一组团、滨江三片区”的城镇和产业“双集中”格局；乡村振兴部分明确“聚力推动城乡融合发展，加快和美乡村示范片建设，建设峒山、四峰山‘一红一绿’和美乡村示范带、四峰山康养民宿群、峒山乡愁民宿群”——这是鄂城区把峒山与四峰山作为“一红一绿”成对示范带加以建设的县级部署，早于2025年省级样板带认定，属A420018片区的前置政策脉络。另含产业链培育、村集体经济百万元村16个、盘活“六废”资源等口径。",
    slug="hb-ez-ec-sanxinsanqiang-2024-xingdongjihua-jiedu",
    instruments="规划,示范带,和美乡村示范片,一红一绿,峒山,四峰山,组团,双集中,城乡融合,共同缔造,千万工程,产业链,村集体经济,六废盘活",
    scope_desc="“两带一组团、滨江三片区”空间格局；建设峒山、四峰山“一红一绿”和美乡村示范带及两个民宿群",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "规划部署", "ymd": "2024-03-29",
             "note": "区级部署建设峒山、四峰山“一红一绿”和美乡村示范带"}],
)

add(
    title="【新闻发布会解读】鄂城区文旅产业融合发展情况",
    url="https://www.echeng.gov.cn/ecqxxgk/bmptlj/qzbm/qwhlyj/fdzdgk/hygq/202409/t20240920_651518.html",
    full_text=body("1b7700c7a0"),
    issuer="鄂城区文化和旅游局", issuer_level="county", doc_type="其他", source_kind="新闻发布",
    credibility="B", county_code=EC, city_code=EZC, issued_ymd="2024-09-19", published_ymd="2024-09-20",
    summary="鄂城区文旅产业融合发展新闻发布会解读稿，给出四峰山所在的汀祖镇片区化建设细节：“汀祖镇四峰山所属各村依托独特的山水优势，发展现代农业、生态旅游，以岳石洪创建AAA景区为切入口，规划建设25公里观光车环线、42公里登山步道、47公里森林马拉松环线，构建农文旅融合发展示范带”；并载明各村做优“白雉山鸡、鄂城黄姜”品牌、引进“乡村创客”“乡村合伙人”与新村民等做法。是四峰山样板带“示范带+环线”空间组织方式的操作层证据。",
    slug="hb-ez-ec-wenlvchanyeronghe-xinwenfabu",
    instruments="示范带,农文旅融合,片区,环线规划,景区创建,乡村创客,乡村合伙人,新村民,特色农产品品牌,全域旅游,连片打造",
    scope_desc="汀祖镇四峰山所属各村；规划25公里观光车环线、42公里登山步道、47公里森林马拉松环线",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "规划部署", "ymd": "2024-09-19",
             "note": "汀祖镇四峰山所属各村构建农文旅融合发展示范带，配套三条环线"}],
)

print("batch4 done")
