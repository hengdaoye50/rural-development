# -*- coding: utf-8 -*-
"""HB02 批次 5：荆州区（环丁家咀水库和美乡村示范片）2 条。"""
import re
from scripts.legacy._hb02_lib import add, body

JZQ = "421003"
JZC = "421000"
A = "A420014"

gb = body("892718b8cb").replace("&mdash;&mdash;", "——").replace("&mdash;", "—").replace("&nbsp;", " ")

add(
    title="荆州区2024年政府工作报告",
    url="http://zwgk.jingzhouqu.gov.cn/26682/103220253/t119220253034/578651.shtml",
    full_text=gb,
    issuer="荆州区人民政府", issuer_level="county", doc_type="报告", source_kind="政策文件",
    credibility="A", county_code=JZQ, city_code=JZC,
    issued_ymd="2024-12-27", published_ymd="2025-03-19",
    summary="荆州区七届人大四次会议政府工作报告（区长张远重）。涉片区化内容两处最关键：一是工作回顾中“乡村建设美丽宜居。省级环丁家咀和美乡村片带试点项目即将完工”，确认A420014片区的省级试点属性与建设进度；二是来年部署“学习运用‘千万工程’经验，深入推进‘一轴两环四线九片’和美乡村片带建设”，这是荆州区本级的片区化空间框架（轴—环—线—片四层结构，九片为片区单元），是理解该区片区命名的关键文本。报告另列农村无害化户厕3455个、垃圾分类自然村57个、生活污水治理率等口径。",
    slug="hb-jz-jzq-2024-zhengfu-gongzuo-baogao",
    instruments="规划,片带,一轴两环四线九片,和美乡村,千万工程,省级试点,人居环境,厕所革命,垃圾分类,乡村旅游,森林康养,生态价值实现",
    scope_desc="全区“一轴两环四线九片”和美乡村片带；省级环丁家咀和美乡村片带试点",
    target_areas=9,
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "试点建设推进", "ymd": "2024-12-27",
             "note": "政府工作报告称省级环丁家咀和美乡村片带试点项目即将完工"}],
)

add(
    title="荆州区环丁家咀水库和美乡村示范片建设项目9标段：导视系统招标（采购）公告",
    url="https://www.ccgp-hubei.gov.cn/notice/202404/notice_3a8a688f6c464ad09e4b8383089a6608.html",
    full_text=body("jzq_zhaobiao"),
    issuer="荆州市荆州区财政局（采购代理：荆州市诚鑫咨询有限公司）",
    issuer_level="county", doc_type="公告", source_kind="政策文件",
    credibility="A", county_code=JZQ, city_code=JZC,
    issued_ymd="2024-04-30", published_ymd="2024-04-30",
    summary="湖北省政府采购网招标公告，首次以工程量清单口径把“环丁家咀水库和美乡村示范片”的标段与村名逐一对齐：项目共9个标段——1标段联山村、2标段北湖桥村、3标段马山镇梅花湾村、4标段马南村、5标段马山镇阴湘城村、6标段马山镇双杨村、7标段双垱村、8标段八岭山镇新场村、9标段导视系统。采购人荆州市荆州区财政局，采购计划备案号荆区采【2024】40号，项目编号JZSJ-202404SZ-022001009，公开招标，合同履行期150日历天。本页为9标段（导视系统）公告，预算金额300.842229万元。可反证示范片至少覆盖荆州区马山镇、八岭山镇及联山村、北湖桥村、双垱村共8个行政村加1个导视系统标段。",
    slug="hb-jz-jzq-huan-dingjiazui-shifanpian-9biaoduan-zhaobiao",
    instruments="财政,政府采购,公开招标,示范片,标段划分,项目编号,采购计划备案,导视系统,面向中小微企业",
    scope_desc="环丁家咀水库和美乡村示范片建设项目共9个标段，8个村标段+1个导视系统标段；本页为9标段，预算300.842229万元",
    budget_wan="300.8422",
    areas=[{"area_id": A, "entity_type": "area", "rel": "primary"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "招标采购", "ymd": "2024-04-30",
             "note": "9个标段招标，采购人荆州区财政局，备案号荆区采【2024】40号"}],
)

print("batch5 done")
