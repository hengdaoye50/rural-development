# -*- coding: utf-8 -*-
"""HB02 批次 3：钟祥市（客店十慢悠享样板带）4 条。"""
from scripts.legacy._hb02_lib import add, body

ZX = "420881"
ZJC = "420800"
A = "A420017"
EV = [{"area_id": A, "entity_type": "area", "event_type": "省级样板带获评", "ymd": "2025-06-05",
       "note": "答复中确认2025年客店镇“十慢悠享·云峰翠谷”示范线获评省级和美乡村样板带"}]

add(
    title="对市政协八届四次会议第8号提案的答复（关于做好美丽乡村建设工作的建议）",
    url="http://www.zhongxiang.gov.cn/art/2025/6/5/art_23310_1163028.html",
    full_text=body("0b05279a8c"),
    issuer="钟祥市农业农村局", issuer_level="county", doc_type="答复", source_kind="部门动态",
    credibility="B", county_code=ZX, city_code=ZJC,
    issued_ymd="2025-06-05", published_ymd="2025-06-05",
    summary="钟祥市农业农村局对市政协八届四次会议第8号提案的答复，明确“客店镇保留乡村原始风貌，围绕‘慢生活’元素，激活‘慢镇’旅游发展潜力，2025年‘十慢悠享·云峰翠谷’示范线获评省级和美乡村样板带荣誉称号”，是A420017片区获省级认定的县级书面确认。同时系统披露钟祥美丽乡村的三项机制：《关于实行分类推进美丽乡村建设的通知》按“整治村、创建村、示范村”三类梯次创建，市财政每年预算安排500万元用于美丽乡村创建奖补；“双百示范”引导机制，打造西客线等百公里美丽乡村建设示范线、提档升级百个示范村；整合30多个项目打包投入和美乡村建设。下一步列明3个省级美丽乡村试点（丰乐镇杨集社区、文集镇大庙村、旧口镇高集村）、八个高速出入口窗口、七条干线。",
    slug="hb-jm-zx-zhengxie-8hao-daofu-meilixiangcun",
    instruments="财政,考核,分类创建,奖补机制,双百示范,示范线,示范村,片区,串点成线连线成片,一村一品,一户一景,微改造精提升,群众主体,党建引领,清洁家园,资源整合",
    scope_desc="全市美丽乡村按整治村/创建村/示范村三类梯次创建，市财政每年500万元奖补；百公里示范线+百个示范村",
    budget_wan="",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=EV,
)

add(
    title="对荆门市十届人大四次会议第144号建议的答复（关于“清洁家园”行动扩面、资金与长效机制优化）",
    url="http://www.zhongxiang.gov.cn/art/2025/6/5/art_23310_1162774.html",
    full_text=body("fe172cde4c"),
    issuer="钟祥市农业农村局", issuer_level="county", doc_type="答复", source_kind="部门动态",
    credibility="B", county_code=ZX, city_code=ZJC,
    issued_ymd="2025-06-05", published_ymd="2025-06-05",
    summary="钟祥市农业农村局对荆门市人大第144号建议的答复。再次确认“2025年客店镇‘十慢悠享·云峰翠谷’示范线获评省级和美乡村样板带荣誉称号”，并给出资金口径：2024年对人居环境整治给予客店镇、张集镇等6个乡镇、温峡水库管理处和南湖新区美丽乡村建设年终奖补资金240万元；对柴湖镇芦席场村、东桥镇墩岭村等4个示范村、九里回族乡示范片农村人居环境整治和美丽乡村建设奖励资金180万元；2025年改厕任务425户、每户奖补1200元。另有“4+1”“6+1”工作机制、“七步工作法”、“1+2+X”组织体系等本地做法。",
    slug="hb-jm-zx-renda-144hao-daofu-qingjiejiayuan",
    instruments="财政,考核,奖补机制,示范片,清洁家园,人居环境,改厕奖补,长效机制,七步工作法,三堆两垛,资金整合",
    scope_desc="年终奖补6个乡镇240万元、4个示范村及九里回族乡示范片180万元；2025年改厕425户每户1200元",
    budget_wan="",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=EV,
)

add(
    title="钟祥市农业农村局2025年工作总结及2026年工作计划",
    url="http://www.zhongxiang.gov.cn/art/2026/2/3/art_12628_1203969.html",
    full_text=body("b103886a21"),
    issuer="钟祥市农业农村局", issuer_level="county", doc_type="总结", source_kind="部门动态",
    credibility="B", county_code=ZX, city_code=ZJC,
    issued_ymd="2026-02-03", published_ymd="2026-02-03",
    summary="钟祥市农业农村局年度工作总结与计划。将“客店镇‘十慢悠享·云峰翠谷’示范线获评省级和美乡村样板带”列为年度成效之一；提出“分类分片建设美丽乡村，打造‘清洁家园’示范点80个，结合‘两圈三线’示范片建设，推动美丽乡村串点成线、连线成片”——“两圈三线”示范片是钟祥本地的片区化提法。产业侧载明国家现代农业产业园（油菜）通过国家中期评估、全国产业强镇（客店葛产业）获批建设、8个“一镇一品”已成规模。",
    slug="hb-jm-zx-nongyeju-2025-zongjie-2026-jihua",
    instruments="规划,片区,两圈三线,示范片,串点成线连线成片,分类分片,清洁家园,一镇一品,产业强镇,现代农业产业园",
    scope_desc="“两圈三线”示范片建设；清洁家园示范点80个",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "年度总结确认", "ymd": "2026-02-03",
             "note": "年度总结将样板带获评列为成效，并提出“两圈三线”示范片建设"}],
)

add(
    title="钟祥市2025年国民经济和社会发展计划执行情况与2026年计划（草案）的报告",
    url="http://www.zhongxiang.gov.cn/art/2025/12/30/art_27943_1231017.html",
    full_text=body("75d0ca823a"),
    issuer="钟祥市人民政府", issuer_level="county", doc_type="报告", source_kind="政策文件",
    credibility="A", county_code=ZX, city_code=ZJC,
    issued_ymd="2025-12-30", published_ymd="2025-12-30",
    summary="钟祥市年度计划执行情况报告（人代会材料）。在总结部分明确“客店‘十慢悠享·云峰翠谷’示范线获评首批‘省级和美乡村样板带’”，是A420017片区获省级命名的政府正式会议文件确认。报告同时给出城市空间格局“一江两湖、两轴引领、三区联动、景城一体”，其中老城片区、城东片区、产业片区属城市更新口径的空间分区，与乡村片区无关，此处仅作区分记录。",
    slug="hb-jm-zx-2025-jihua-zhixing-2026-jihua-baogao",
    instruments="规划,样板带,省级命名,一江两湖,三区联动,景城一体,乡村振兴",
    scope_desc="全市年度计划执行情况；确认客店样板带获省级认定",
    areas=[{"area_id": A, "entity_type": "area", "rel": "support"}],
    events=[{"area_id": A, "entity_type": "area", "event_type": "省级样板带获评", "ymd": "2025-12-30",
             "note": "计划执行情况报告确认获评首批省级和美乡村样板带"}],
)

print("batch3 done")
