# -*- coding: utf-8 -*-
"""HB02 批次 2：京山市（环惠亭湖示范片/样板带）7 条。"""
from scripts.legacy._hb02_lib import add, body

JS = "420882"
JSC = "420800"
A = "A420007"

add(
    title="京山市行政审批局关于京山市“环惠亭湖”美丽乡村示范片建设试点项目初步设计方案的批复",
    url="http://www.jingshan.gov.cn/art/2023/4/18/art_15431_977130.html",
    full_text=body("85cb144c94"),
    issuer="京山市行政审批局", issuer_level="county", doc_type="批复", source_kind="政策文件",
    credibility="A", county_code=JS, city_code=JSC, doc_no="京审批字〔2023〕78号",
    issued_ymd="2023-04-18", published_ymd="2023-04-18",
    summary="京山市行政审批局对“环惠亭湖”美丽乡村示范片建设试点项目初步设计方案的正式批复（京审批字〔2023〕78号，项目代码2302-420882-04-01-529878）。建设地点逐村列明：新市街道白谷洞村、高岭村、鄢河村、荷花堰村、丁家塝村，温泉街道莲山村、水峡口村，孙桥镇梭罗河村、花苑台村、冯家岭村，共10个美丽乡村；升级改造全线29.6公里双车道路基路面并配套基础设施、公共服务设施、产业融合、人居环境提升，总用地约258113.5平方米（约387.17亩），建设期24个月，概算总投资11000.7万元，资金来源为财政资金。是A420007片区最硬的县级设立/立项依据。",
    slug="hb-jm-js-huanhuitinghu-chubusheji-pifu",
    instruments="财政,规划,片区,示范片,项目审批,初步设计,基础设施,人居环境,产业融合,乡村振兴试点",
    scope_desc="建设地点覆盖新市街道5村、温泉街道2村、孙桥镇3村共10个美丽乡村，全线29.6公里",
    budget_wan="11000.7",
    areas=[{"area_id": A, "entity_type": "area", "rel": "primary"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "批复立项", "ymd": "2023-04-18",
             "note": "京审批字〔2023〕78号批复初步设计方案，概算总投资11000.7万元"}],
)

add(
    title="关于要求拨付“环惠亭湖”美丽乡村示范片建设项目资金",
    url="http://www.jingshan.gov.cn/art/2022/10/25/art_24623_923458.html",
    full_text=body("90611798aa"),
    issuer="京山市财政局", issuer_level="county", doc_type="其他", source_kind="部门动态",
    credibility="B", county_code=JS, city_code=JSC,
    issued_ymd="2022-10-25", published_ymd="2022-10-25",
    summary="京山市财政局向市政府报送的资金拨付请示。关键信息：2021年11月省财政厅《关于公布2022年度美丽乡村示范片建设试点县名单的通知》（鄂财农村发〔2021〕24号）确定京山等11个县（市、区）为2022年度全省美丽乡村示范片建设试点县——这是“环惠亭湖”示范片的省级来源依据。本次需拨付项目资金1300.39万元，其中省财政奖补500万元、市本级配套800.39万元，并逐村列出分配数额（花苑台200万、冯家岭150万、梭罗河150万、白谷洞300.39万、荷花堰150万、水峡口100万、莲山100万）。",
    slug="hb-jm-js-huanhuitinghu-xiangmu-zijin-bofu",
    instruments="财政,专项资金,示范片,试点县,省财政奖补,市本级配套,资金分配",
    scope_desc="“环惠亭湖”美丽乡村示范片建设项目资金1300.39万元，逐村分配",
    budget_wan="1300.39",
    areas=[{"area_id": A, "entity_type": "area", "rel": "primary"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "资金下达", "ymd": "2022-10-25",
             "note": "拨付示范片项目资金1300.39万元（省奖补500万+市配套800.39万）"}],
)

add(
    title="关于预拨环惠亭湖美丽乡村建设示范片规划设计费",
    url="http://www.jingshan.gov.cn/art/2022/6/9/art_24623_922218.html",
    full_text=body("b5a5356990"),
    issuer="京山市财政局", issuer_level="county", doc_type="其他", source_kind="部门动态",
    credibility="B", county_code=JS, city_code=JSC,
    issued_ymd="2022-06-09", published_ymd="2022-06-09",
    summary="京山市财政局关于预拨环惠亭湖美丽乡村建设示范片规划设计费的请示。依据《省财政厅关于提前下达2022年农村综合改革转移支付资金的通知》（鄂财农村发〔2021〕17号）及省财政厅督办要求，须在8月底前完成美丽乡村建设示范片规划设计任务；经公开招标由华茗设计集团有限公司中标，合同标的额147.8万元，分6次支付，本次预付20%即29.56万元。可反证该示范片确曾单独编制规划设计。",
    slug="hb-jm-js-huanhuitinghu-guihua-shejifei",
    instruments="财政,规划,片区规划编制,示范片,政府采购,公开招标,转移支付",
    scope_desc="示范片规划设计合同标的额147.8万元，分6次支付，本次预付29.56万元",
    budget_wan="147.8",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "规划编制", "ymd": "2022-06-09",
             "note": "华茗设计集团有限公司中标示范片规划设计，合同标的额147.8万元"}],
)

add(
    title="京山市财政局关于下达2023年和美乡村建设本级配套资金的通知",
    url="http://www.jingshan.gov.cn/art/2023/10/23/art_2016_1223210.html",
    full_text=body("f97a9fb8b5"),
    issuer="京山市财政局", issuer_level="county", doc_type="通知", source_kind="政策文件",
    credibility="A", county_code=JS, city_code=JSC,
    issued_ymd="2023-10-23", published_ymd="2023-10-23", doc_no="",
    summary="依据《省财政厅关于下达2023年省级农村综合配套改革转移支付资金的通知》（鄂财农村发〔2023〕2号），经市政府同意下达和美乡村4个村共400万元本级配套资金：孙桥镇横岭铺村、曹武镇曹武村、钱场镇深沟村、雁门口镇长岗村各100万元。属京山市和美乡村建设的资金链条文件，但未点名环惠亭湖示范片，故不挂接片区。",
    slug="hb-jm-js-2023-hemeixiangcun-peitao-zijin",
    instruments="财政,专项资金,和美乡村,转移支付,本级配套,资金下达",
    scope_desc="4个和美乡村各100万元，合计400万元",
    budget_wan="400",
)

add(
    title="环惠亭湖美丽乡村示范片区旅游环线即将贯通",
    url="http://www.jingshan.gov.cn/art/2025/8/8/art_24194_1169899.html",
    full_text=body("64456a48be"),
    issuer="京山市交通运输局", issuer_level="county", doc_type="动态", source_kind="部门动态",
    credibility="B", county_code=JS, city_code=JSC,
    issued_ymd="2025-08-08", published_ymd="2025-08-08",
    summary="京山市交通运输局工作动态：环惠亭湖美丽乡村示范片区旅游环线全长29.6公里，位于温泉街道、孙桥镇、新市街道，围绕惠亭水库及京山市西北侧，接新长线往孙桥镇方向连接347国道。第一段17.1公里途经水峡口、横岭铺、冯家岭等村已于2023年12月完工；第二段12.5公里途经花苑台、梭罗河、丁家塝、荷花堰、四岭、白谷洞等村于2025年7月完成路面工程。反映示范片基础设施落地进度。",
    slug="hb-jm-js-huanhuitinghu-lvyouhuanxian-guantong",
    instruments="基础设施,旅游环线,示范片,全域旅游,四好农村路,片区建设",
    scope_desc="旅游环线全长29.6公里，分两段实施，覆盖水峡口、横岭铺、冯家岭、花苑台、梭罗河、丁家塝、荷花堰、四岭、白谷洞等村",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "项目完工", "ymd": "2025-07",
             "note": "旅游环线第二段12.5公里完成路面工程，全线即将贯通"}],
)

add(
    title="关于市政协二届二次会议第2023008号提案的答复（关于大力发展环惠亭湖农文旅产业）",
    url="http://www.jingshan.gov.cn/art/2023/8/25/art_8618_1025836.html",
    full_text=body("591a991747"),
    issuer="京山市文化和旅游局", issuer_level="county", doc_type="答复", source_kind="部门动态",
    credibility="B", county_code=JS, city_code=JSC,
    issued_ymd="2023-08-25", published_ymd="2023-08-25",
    summary="京山市文化和旅游局对市政协二届二次会议第2023008号提案“关于大力发展环惠亭湖农文旅产业”的答复，是本县环湖片区口径最完整的一份非正式文件。明确“结合环惠亭湖周边26个美丽乡村的实际情况”编制环惠亭湖农文旅发展规划，待市乡村振兴局环湖相关村项目入库和规划文件出台后聘请专业团队规划；逐项回应规划衔接、资源普查、基础设施（水利湖泊局整合大中型水库移民后期扶持资金对高岭、冯家岭、高潮等15个村开展人居环境整治，已验收7个村）、精品节点（对节白蜡4A创建、天沐温泉）、新型业态（一村一品民宿、夜游经济）、市场化运营（村集体成立白谷烟树文化旅游公司）。",
    slug="hb-jm-js-zhengxie-2023008-huanhuitinghu-daofu",
    instruments="规划,片区规划,农文旅融合,一村一品,美丽乡村,人居环境,移民后扶持资金,资源普查,4A景区创建,市场化运营,村集体公司,夜游经济",
    scope_desc="环惠亭湖周边26个美丽乡村；基础设施覆盖高岭、冯家岭、高潮等15个村",
    target_areas="",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "规划部署", "ymd": "2023-08-25",
             "note": "答复明确结合环湖26个美丽乡村编制环惠亭湖农文旅发展规划"}],
)

add(
    title="京山市整县推进美丽乡村建设，奋力打造美丽先行区样板",
    url="http://www.jingshan.gov.cn/art/2025/6/4/art_24148_1156331.html",
    full_text=body("ad447b7200"),
    issuer="荆门市生态环境局京山分局", issuer_level="county", doc_type="其他", source_kind="部门动态",
    credibility="B", county_code=JS, city_code=JSC,
    issued_ymd="2025-06-04", published_ymd="2025-06-04",
    summary="荆门市生态环境局京山分局的典型经验材料。按湖北省美丽乡村建设实施方案要求整县推进美丽乡村建设，提出“确保宜居宜业和美乡村达到197个”，推进“厕污垃”综合治理（建改农村旱厕800座以上、无害化卫生厕所普及率99%、生活垃圾分类自然村占比60%以上）。是京山市和美乡村建设的县域总量口径来源，可作为样板带所在县域的政策背景。",
    slug="hb-jm-js-zhengtixian-meili-meicun-jianshe",
    instruments="规划,整县推进,美丽乡村,和美乡村,厕污垃治理,人居环境,生态文明示范县,清洁家园",
    scope_desc="全市宜居宜业和美乡村达197个",
    target_areas="",
)

print("batch2 done")
