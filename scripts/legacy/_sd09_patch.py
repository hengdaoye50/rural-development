"""Patch metadata (title/issuer/summary/instruments/areas/...) on already-appended records."""
import io, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")

PATCH = {
    "nid=216322": {
        "title": "蒙阴县人民政府办公室关于2026年第一季度县《政府工作报告》重点任务推进落实情况的通报",
        "doc_no": "",
        "issuer": "蒙阴县人民政府办公室",
        "issuer_level": "county",
        "issued_ymd": "2026-05-06",
        "published_ymd": "",
        "doc_type": "通报",
        "instruments": "考核,组织,金融,片区授信,共富工坊,共富试验区,三资管理,片区组团",
        "budget_wan": "3000",
        "summary": "蒙阴县人民政府办公室2026年5月6日通报第一季度县《政府工作报告》重点任务推进落实情况，附任务汇总表逐条列出牵头单位与进展：推荐垛庄镇华润希望小镇片区争创市级乡村振兴共富试验区、方案已报市农业农村局；起草《金融系统强化「融资+融智」助力乡村振兴片区建设工作方案》，为1个有融资需求的片区建设项目授信3000万元；做优做强现有102家共富工坊；实施环蒙山北线、汶平线公路旅游服务提升工程。",
        "areas": [{"area_id": "A370116", "entity_type": "area", "rel": "support"}],
        "events": [{"area_id": "A370116", "entity_type": "area", "event_type": "申报",
                    "ymd": "2026-05-06", "note": "垛庄镇华润希望小镇片区争创市级乡村振兴共富试验区，方案已报市农业农村局"}],
    },
    "1742/307919": {
        "title": "筵宾镇：奋战十五五 挺进中上游 奋力谱写筵宾高质量发展新篇章（政务访谈）",
        "issuer": "莒南县筵宾镇人民政府",
        "issuer_level": "town",
        "doc_type": "动态",
        "instruments": "组织,产业,考核,规划,片区党建工作协调委员会,周例会月调度季总结,好客筵宾",
        "summary": "莒南县筵宾镇党委副书记、镇长郇恒健政务访谈。明确把「好客筵宾」片区建设作为当年乡村振兴的首要任务，年初专门成立片区党建工作协调委员会，由党委副书记牵头主抓、1名副科级干部和2名年轻骨干全脱产靠上抓，明确6项核心职责，落实周例会、月调度、季总结制度，先后召开专题会议13次、会商解决问题36项。",
        "areas": [{"area_id": "A370038", "entity_type": "area", "rel": "support"}],
        "events": [{"area_id": "A370038", "entity_type": "area", "event_type": "组织设立",
                    "ymd": "", "note": "年初成立片区党建工作协调委员会，镇党委副书记牵头主抓"}],
    },
    "1742/60663": {
        "title": "党建引领发展 创新提质增效 全面打造高质量发展新高地（道口镇政务访谈）",
        "issuer": "莒南县道口镇人民政府",
        "issuer_level": "town",
        "doc_type": "动态",
        "instruments": "组织,财政,产业,片区党委,光伏增收片区,网格化治理,三务公开",
        "budget_wan": "1200",
        "summary": "莒南县道口镇党委书记李超政务访谈。载明以党建引领城乡基层网格化社会治理为抓手成立5个片区党委；在帮扶经济薄弱村上采取「党委政府+企业+经济薄弱村」合作模式，在全镇划分5个光伏增收片区，在6个村先行试点建设光伏增收典型示范片区，已基本完成投资1200万元打造的先行样板增收片区，安装光伏电站200余座、装机容量3.4MW。",
        "areas": [{"area_id": "A370038", "entity_type": "area", "rel": "support"}],
        "events": [{"area_id": "A370038", "entity_type": "area", "event_type": "组织设立",
                    "ymd": "", "note": "以网格化治理为抓手成立5个片区党委"}],
    },
    "1742/301319": {
        "title": "茶韵栗香满洙边 实干争先谱新篇（政务访谈）",
        "issuer": "莒南县洙边镇人民政府",
        "issuer_level": "town",
        "doc_type": "动态",
        "instruments": "组织,产业,治理,片区建设,五项日常管理制度,横向指挥部纵向网格化,组织连片共建",
        "summary": "莒南县洙边镇党委副书记、镇长昝金龙政务访谈。明确把乡村振兴片区建设作为「头号工程」，坚持组织连片共建、产业抱团发展、治理联动联解，已建成「茶韵栗香」示范片区，正高标准推进「栗王谷」省级乡村振兴片区建设；组织上探索基层组织「五项日常管理制度」，依托「三强联动分析表」定期通报动态数据，采取「横向指挥部、纵向网格化」双线工作模式。",
        "areas": [{"area_id": "A370038", "entity_type": "area", "rel": "support"}],
        "events": [],
    },
    "1333/401376": {
        "title": "莒南：省派第一书记多元举措谋发展",
        "issuer": "临沂市人民政府办公室",
        "issuer_level": "city",
        "published_ymd": "2025-08-02",
        "doc_type": "动态",
        "instruments": "组织,产业,数字,第一书记,党建+产业,一村一品,片区建设",
        "summary": "临沂市政府办公室「区县动态」栏目发布（索引号1585729837/zfb/2025-0000139）。载明莒南县筵宾镇省派第一书记紧扣「党建引领、产业升级、强村富民」主线推进片区建设：创新「党建+产业」模式培育「一村一品」；复制泉龙村经验在薛家水磨村建「好客筵宾」电商直播基地，计划培养10名本土主播，开发溯源系统，首办乡村振兴博览会线上销售额破10万元。",
        "areas": [{"area_id": "A370038", "entity_type": "area", "rel": "support"}],
        "events": [],
    },
    "10394/252302": {
        "title": "蒙阴：焕新提质 让蒙山「流量」变「留量」",
        "issuer": "蒙阴县农业农村局",
        "issuer_level": "county",
        "published_ymd": "2026-11-06",
        "doc_type": "动态",
        "instruments": "规划,产业,文旅融合,民宿集聚区,激活蒙山",
        "summary": "蒙阴县农业农村局发布（索引号mengyinxian00446553-4/20261106-00002）。蒙阴县落实「激活蒙山」战略、以「1+7」文旅融合为引推进民宿提质：规划环蒙山、孟良崮、岱崮、云蒙湖4大民宿集聚区，围绕「环蒙山精品民宿带」打造椿树沟、百花峪等民宿集群，民宿集聚区年接待游客超110万人次、带动旅游收入1.2亿元，全县有省级星级民宿19家、市级「沂蒙乡愁」民宿34家。",
        "areas": [{"area_id": "A370185", "entity_type": "area", "rel": "mention"}],
        "events": [],
    },
}


def main():
    recs = []
    with io.open(TARGET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    n = 0
    for o in recs:
        for key, patch in PATCH.items():
            if key in o.get("url", ""):
                o.update(patch)
                n += 1
                print("PATCHED:", o["title"][:52])
                break
    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as f:
        for o in recs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("records:", len(recs), "patched:", n)


if __name__ == "__main__":
    main()
