# -*- coding: utf-8 -*-
"""HB02 批次 6：省级普适文件（省委一号文件，含“片区化推进乡村振兴”总口径）。"""
from scripts.legacy._hb02_lib import add, body

add(
    title="中共湖北省委 湖北省人民政府关于锚定农业农村现代化扎实推进乡村全面振兴的实施意见（2026年省委一号文件）",
    url="https://nyt.hubei.gov.cn/dtyw/202603/t20260315_5892334.shtml",
    full_text=body("fb7c406de0"),
    issuer="中共湖北省委、湖北省人民政府", issuer_level="province", doc_type="意见",
    source_kind="政策文件", credibility="A", county_code="", city_code="",
    issued_ymd="2026-02-16", published_ymd="2026-03-15",
    summary="2026年湖北省委一号文件全文（省农业农村厅网站发布）。涉片区化的总口径在“推进宜居宜业和美乡村建设”部分：“深入学习运用‘千万工程’经验，分类有序、片区化推进乡村振兴，逐步提高农村基础设施完备度、公共服务便利度、人居环境舒适度”——这是湖北省级层面把“片区化”写入一号文件的依据，也是本库HB02各县样板带/片带建设的上位政策。文件另含城乡要素双向流动、五级书记抓乡村振兴、市州党政领导班子乡村振兴实绩考核、“楚天英才计划”乡村振兴人才等条款。全省普适文件，不点名具体片区。",
    slug="hb-sheng-2026-shouyihao-wenjian-pianquhua",
    instruments="规划,片区化推进乡村振兴,千万工程,和美乡村,人居环境,城乡融合,城乡要素双向流动,考核,人才,财政,金融,土地",
    scope_desc="全省；提出“分类有序、片区化推进乡村振兴”",
    areas=[],
    events=[],
)

print("batch6 done")
