# -*- coding: utf-8 -*-
"""ZJ-batch05: append named village-cluster areas to ZJ clean by_province CSVs.
Only writes data/clean/by_province/ZJ-{area,source,area_source_map,area_region_map}.csv
and raw snapshots under data/raw/330000-浙江/. Does NOT touch root tables.
"""
import csv, os, json
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "data", "clean", "by_province")
RAW = os.path.join(ROOT, "data", "raw", "330000-浙江")
NOW = "2026-09-30T16:00:00+08:00"
CB = "ZJ-batch05"

AREA_FIELDS = [
    "area_id","name","name_norm","type_code","type_primary_note","tags",
    "province_code","city_code","county_code","town_codes","cover_desc",
    "scale_villages","scale_towns","founded_ymd","founded_precision","status",
    "lead_org","issuer","summary","parent_area_key","first_source_id",
    "record_state","created_at","updated_at","created_by",
]
SRC_FIELDS = [
    "source_id","area_id","url","title","publisher","published_ymd","excerpt",
    "fetched_at","credibility","local_path","hash_sha256",
]
MAP_FIELDS = ["area_id","source_id","entity_type","rel"]
REG_FIELDS = ["area_id","level","region_code","region_name"]

# ── raw snapshots ──────────────────────────────────────────────────────────
RAW_DIRS = {
    "20260909-tz-pianqu-zutuan": {
        "url": "http://zj.people.com.cn/n2/2026/0909/c186327-41690635.html",
        "title": "从「单村独奏」到「片区交响」台州片区组团的共富之路",
        "publisher": "台州日报/人民网浙江频道",
        "published_ymd": "2026-09-09",
        "credibility": "A",
        "excerpt": (
            "台州片区组团发展综述。天台县赤城街道大塔后片区2018年率先探索，塔后村接待游客58万人次。"
            "天台后岸片区由街头镇后岸村、张家桐村、遮山村与龙溪乡黄水村、寒山村、寒岩村、始丰源村7个村抱团，"
            "年接待游客超100万人次。此后塔后、安科、张思等片区迅速崛起。临海「江南·溪望谷」联动香年溪沿岸"
            "康平、垟路、宿仙、汇丰、香年、小溪6个村，2023年试营业以来各村集体收入均突破100万元。"
            "椒江「大陈片区」旅游全岛化、黄岩「柔川片区」「陪伴式」规划、三门「亭旁片区」「古村新生」。"
            "玉环干江镇以上栈头村为核心串联炮台、白马岙等8个沿海村庄组建大栈头重点村组团片区，"
            "重点村上栈头村累计创收超4000万元。"
        ),
    },
    "20260509-nb-xianchanghui": {
        "url": "https://zj.cnr.cn/mlnb/hmxc/20260509/t20260509_527614970.shtml",
        "title": "浙江省深化乡村片区组团发展现场会在宁波召开",
        "publisher": "央广网/宁波市农业农村局",
        "published_ymd": "2026-05-09",
        "credibility": "A",
        "excerpt": (
            "5月8日全省深化乡村片区组团发展现场会在宁波奉化召开，发布2026年第一批省级重点村名单。"
            "宁波40个省级片区党建联席会议全覆盖，慈溪翠屏梅堰片区组建杨梅共富工坊联盟带动1500户梅农。"
            "江北云湖片区整体运营后4个薄弱村收入翻三倍，形成「文化大院」「云湖生活」片区IP。"
            "与会代表考察奉化雪窦乡履片区东山村、大滕头片区林家村、金溪五村片区蒋家池头村三个考察点。"
        ),
    },
    "20260509-zjol-xueyushi": {
        "url": "http://zjnews.zjol.com.cn/yc/qmt/202605/t20260509_31651097.shtml",
        "title": "从「单打独斗」到「组团出道」浙江乡村发展走出新路",
        "publisher": "浙江在线",
        "published_ymd": "2026-05-09",
        "credibility": "B",
        "excerpt": (
            "宁波奉化东山村是雪窦乡片区的重点村，引入专业运营团队盘活闲置农房60余栋，建成民宿28家，"
            "带动村集体增收60万元。大滕头片区走产业富民路子，林家村融入片区产业体系，"
            "水蜜桃全产业链产值达20亿元。蒋家池头村所处的金溪五村片区有「133」青年入乡机制。"
            "现场公布2026年第一批省级重点村名单，确定杭州市西湖区转塘街道长埭村等94个村为2026年第一批省级重点村。"
        ),
    },
    "20260423-jh-10-shengjidiancun": {
        "url": "http://zj.people.com.cn/n2/2026/0423/c186327-41560462.html",
        "title": "金华市乡村片区组团发展添引擎",
        "publisher": "金华日报/人民网浙江频道",
        "published_ymd": "2026-04-23",
        "credibility": "A",
        "excerpt": (
            "浙江省农业农村厅公布2026年第一批省级重点村名单，金华市共10个村上榜，数量居全省第三。"
            "这10个村分别是婺城区长山乡卢家村、金东区曹宅镇岩后村、兰溪市诸葛镇诸葛村、东阳市南马镇花园村、"
            "义乌市上溪镇苦竹塘村、永康市龙山镇桥下东村、浦江县虞宅乡新光村、武义县熟溪街道溪里村、"
            "磐安县盘峰乡榉溪村、金华开发区罗埠镇后张村。全市推进60个重点村组团片区建设，其中33个列入省级培育名单。"
        ),
    },
    "20260506-hy-huayuan-pianqu": {
        "url": "https://www.gardencn.com/m/article.php?id=3419",
        "title": "2026年第一批省级重点村名单公布花园村榜上有名",
        "publisher": "花园集团",
        "published_ymd": "2026-05-06",
        "credibility": "B",
        "excerpt": (
            "花园村作为产教共融·研旅花园片区的重点村，依托红木家居产业集群、省级研学示范基地以及"
            "横店影视产业溢出效应，串联上安恬村、下安恬村、泉府村、下格村、联合村、紫溪村、大联村、"
            "梨枫村、山联村等周边9个地理区域相邻、资源禀赋互补的行政村，打造以「产教融合赋能、"
            "文旅双链驱动」为特色的共富片区组团。东阳市农业农村局表示花园片区将推动产业共建、"
            "资源共享、利益共赢五大机制落地。"
        ),
    },
    "20260419-sx-6-cun": {
        "url": "http://zj.people.com.cn/n2/2026/0419/c186327-41556569.html",
        "title": "2026年首批省级重点村公布绍兴六村上榜",
        "publisher": "绍兴日报/人民网浙江频道",
        "published_ymd": "2026-04-19",
        "credibility": "A",
        "excerpt": (
            "2026年第一批省级重点村名单公布，绍兴市共6个村上榜：越城区东浦街道南村村、柯桥区王坛镇东村村、"
            "上虞区道墟街道新屯南村、诸暨市陈宅镇石壁湖村、嵊州市三界镇长桥村、新昌县儒岙镇会墅岭村。"
            "南村村深耕酒文化与戏曲底蕴，联同东浦村、王城寺村、壶觞村等村打造「酒香有戏」片区；"
            "东村村以梅花为媒，联同王城村、丹家村等村构建「踏雪寻梅」生态文旅片区。"
            "至此绍兴市已有18个村入选省级重点村。"
        ),
    },
    "20260102-jhkq-paixitong": {
        "url": "https://www.zj.chinanews.com.cn/jzkzj/2026-01-02/detail-iheymhtf5109268.shtml",
        "title": "浙江金华开发区：农文旅融合绘就乡村振兴新画卷",
        "publisher": "中新网浙江",
        "published_ymd": "2026-01-02",
        "credibility": "B",
        "excerpt": (
            "金华开发区扎实推进「婺美共富」发展轴及多个和美乡村组团片区建设，其中派溪童片区入选省级重点村片区。"
            "汤溪镇以「汤溪十景」品牌为核心，通过「月月有主题、季季有热点」活动矩阵推动文旅融合。"
            "乡村振兴部正系统整合「1234+N」资源矩阵，以汤溪镇为核心串联关键节点与特色村落，构建全域发展格局。"
        ),
    },
    "20260120-hz-pianqu-zutuan": {
        "url": "https://hwyst.hangzhou.com.cn/xwfb/content/2026-01/20/content_9164880.htm",
        "title": "从「单打独斗」到「攥指成拳」杭州乡村片区组团闯出共富新路",
        "publisher": "杭州网/杭州通",
        "published_ymd": "2026-01-20",
        "credibility": "B",
        "excerpt": (
            "建德市航头镇「139乡宿」片区组团2026年1月启动建设，以航川村「139乡宿」为核心联动周边五个行政村，"
            "构建「一心」「两园」「多点」乡村振兴示范片区。临安区高虹镇石门村、龙上村、大山村共同打造"
            "「龙门秘境」片区组团，石门村定位「古村寻韵+红色研学」、龙上村聚焦「奇石探险+户外畅玩」、"
            "大山村深耕「梯田康养+松林度假」。桐庐县「云溪畲韵」片区突出民族文化特色打造「西湖边的畲乡」品牌。"
            "截至目前杭州市已完成110个片区总体规划，全面启动50个片区组团建设。"
        ),
    },
    "20260202-xj-sida-jingpin": {
        "url": "https://tidenews.com.cn/news.html?id=3361419",
        "title": "仙居以片区组团发展激活全域旅游拼好四大拼图绽放一城芳华",
        "publisher": "潮新闻/浙江日报",
        "published_ymd": "2026-02-02",
        "credibility": "B",
        "excerpt": (
            "2025年以来，仙居以神仙居景区、下汤遗址、永安溪、321省道为核心和轴线，推进环神仙居、万年文化、"
            "高铁滨溪、东部运动四大精品片区组团发展，推动片区内10个乡镇的25个重点村实现景区化转型。"
            "东部运动精品片区以321省道为主轴联动白塔、上张、朱溪等乡镇。淡竹乡下陈朱村引入高端民宿，"
            "横溪镇上江垟村打造非遗特色村，朱溪镇杨丰山村建设运动驿站。四大精品片区组团已启动项目69个，"
            "引进业态74个，撬动投资9亿多元。"
        ),
    },
    "20250619-hn-dayuan": {
        "url": "http://www.news.cn/photo/20250619/7585def8b00c4529b11bed34f716a221/c.html",
        "title": "浙江海宁盐官推动乡村片区组团发展",
        "publisher": "新华网",
        "published_ymd": "2025-06-19",
        "credibility": "A",
        "excerpt": (
            "浙江省海宁市盐官镇桃园村坚持推进「大桃园」乡村片区组团发展模式，跨镇联动周边11个村，"
            "拓展「培训+研学+文创+旅游」等业态，打造花卉、稻米、果蔬3大亿元产业。"
            "「大桃园」横跨三镇，通过组织共建在规划上取长补短，在产业上以桃园村为核心辐射带动。"
        ),
    },
    "20260416-hn-chaoshan": {
        "url": "http://www.xinhuanet.com/photo/20260416/6b535cc591144a49b8ddfbeb1985eeac/c.html",
        "title": "浙江海宁：推进片区组团发展助力乡村振兴",
        "publisher": "新华网",
        "published_ymd": "2026-04-16",
        "credibility": "A",
        "excerpt": (
            "海宁市黄湾镇以尖山村为重点村，联合周边多个行政村组建「潮起尖山」组团片区，规划总面积47.5平方公里，"
            "串联「自然潮、农业潮、运动潮、乡村潮」四大特色主题，推动片区组团发展助力乡村振兴。"
        ),
    },
    "20251119-hn-shida-pianqu": {
        "url": "https://tidenews.com.cn/news.html?id=3303721",
        "title": "「千万」新潮起海宁丨「千万工程」给海宁城乡带来了什么？",
        "publisher": "潮新闻",
        "published_ymd": "2025-11-19",
        "credibility": "B",
        "excerpt": (
            "海宁已形成十大片区组团的「八大模式」，以重点村辐射带动周边56个村和17个社区协同发展。"
            "在「大博儒桥」组团片区，核心村博儒桥村带动星火村、云龙村等协同发展。"
            "海宁以「大桃园」「大博儒桥」等片区组团发展模式为区域共同富裕蹚出新路径。"
        ),
    },
}

# ── area rows ──────────────────────────────────────────────────────────────
AREAS = [
    # Taizhou
    dict(area_id="A330368", name="大塔后片区", name_norm="大塔后片区", type_code="T05",
         type_primary_note="台州片区组团先行者2018年探索", tags="发展轴;重点村组团;民宿;天台",
         city_code="331000", county_code="331023", town_codes="赤城街道",
         cover_desc="天台县赤城街道大塔后片区以塔后村为核心", scale_villages="",
         founded_ymd="2018", founded_precision="year", status="运行中", lead_org="",
         issuer="台州市农业农村局",
         summary="台州片区组团发展模式的先行者「大塔后片区」2018年开始探索实践。塔后村2025年接待游客58万人次，村集体收入286万元，村民人均可支配收入6.8万元。省320名单归属待核。",
         first_source_id="S087"),
    dict(area_id="A330369", name="后岸片区", name_norm="后岸片区", type_code="T05",
         type_primary_note="天台跨乡镇7村抱团文旅片区", tags="重点村组团;文旅;跨乡镇;天台",
         city_code="331000", county_code="331023", town_codes="街头镇;龙溪乡",
         cover_desc="街头镇后岸村、张家桐村、遮山村与龙溪乡黄水村、寒山村、寒岩村、始丰源村7个村抱团",
         scale_villages="7", founded_ymd="2018", founded_precision="year", status="运行中",
         lead_org="", issuer="台州市农业农村局",
         summary="天台后岸片区由街头镇后岸村、张家桐村、遮山村与龙溪乡黄水村、寒山村、寒岩村、始丰源村7个村抱团发展，年接待游客超100万人次，旅游总收入超1.2亿元。2018年3月跨乡镇研讨会达成组团共识。省320名单归属待核。",
         first_source_id="S087"),
    dict(area_id="A330370", name="江南溪望谷片区", name_norm="江南溪望谷片区", type_code="T05",
         type_primary_note="临海国资领投+企业运营+村村入股片区联营矩阵", tags="重点村组团;国资;文旅;临海",
         city_code="331000", county_code="331082", town_codes="江南街道",
         cover_desc="香年溪沿岸康平、垟路、宿仙、汇丰、香年、小溪6个村",
         scale_villages="6", founded_ymd="2023", founded_precision="year", status="运行中",
         lead_org="", issuer="台州市农业农村局",
         summary="临海「江南·溪望谷」项目2023年试营业，香年溪沿岸康平、垟路、宿仙、汇丰、香年、小溪6个村通过「国资领投+企业运营+村村入股」片区联营矩阵发展，各村集体收入均突破100万元。康平村集体经济从52万元增至2025年309万元。省320名单归属待核。",
         first_source_id="S087"),
    dict(area_id="A330371", name="大陈片区", name_norm="大陈片区", type_code="T05",
         type_primary_note="椒江海岛旅游全岛化片区", tags="重点村组团;海岛;文旅;椒江",
         city_code="331000", county_code="331002", town_codes="大陈镇",
         cover_desc="椒江区大陈岛旅游全岛化片区", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="待核", lead_org="",
         issuer="台州市农业农村局",
         summary="椒江「大陈片区」推进旅游全岛化，大陈岛甲午岩景区创成国家4A级景区，建成两岸乡情文化馆、青少年研学中心、垦荒剧场等27个重点项目。省320名单归属待核。",
         first_source_id="S087"),
    dict(area_id="A330372", name="柔川片区", name_norm="柔川片区", type_code="T05",
         type_primary_note="黄岩陪伴式规划古村活态片区", tags="重点村组团;古村;文旅;黄岩",
         city_code="331000", county_code="331003", town_codes="屿头乡",
         cover_desc="黄岩区屿头乡柔川景区周边", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="待核", lead_org="",
         issuer="台州市农业农村局",
         summary="黄岩「柔川片区」采用「陪伴式」规划推进片区组团，柔川景区为国家AAAA级旅游景区，地处长潭水库上游。与第二批省级重点村沙滩村（屿头乡）相关，片区正式全称待核。",
         first_source_id="S087"),
    dict(area_id="A330373", name="亭旁片区", name_norm="亭旁片区", type_code="T05",
         type_primary_note="三门古村新生片区", tags="重点村组团;古村;红色;三门",
         city_code="331000", county_code="331022", town_codes="亭旁镇",
         cover_desc="三门县亭旁镇古村新生片区", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="待核", lead_org="",
         issuer="台州市农业农村局",
         summary="三门「亭旁片区」以「古村新生」为主题推进片区组团。亭旁镇为红色古镇、亭旁起义发生地。省320名单归属待核。",
         first_source_id="S087"),
    dict(area_id="A330374", name="大栈头片区", name_norm="大栈头片区", type_code="T05",
         type_primary_note="玉环干江重点村组团片区正式名", tags="重点村组团;滨海;持股共富;玉环",
         city_code="331000", county_code="331081", town_codes="干江镇",
         cover_desc="以上栈头村为核心串联炮台、白马岙等8个沿海村庄",
         scale_villages="8", founded_ymd="", founded_precision="unknown", status="运行中",
         lead_org="", issuer="台州市农业农村局",
         summary="玉环市干江镇以上栈头村为核心串联炮台、白马岙等8个沿海村庄组建大栈头重点村组团片区。上栈头村率先探索「4951农民持股共富模式」，累计创收超4000万元，村民累计分红1100万元。与A330160干江滨海风光片区疑为同一单元不同名称，分别记待核。",
         parent_area_key="A330160", first_source_id="S087"),
    # Xianju four
    dict(area_id="A330375", name="环神仙居精品片区", name_norm="环神仙居精品片区", type_code="T05",
         type_primary_note="仙居四大精品片区组团之一", tags="精品片区;文旅;神仙居;仙居",
         city_code="331000", county_code="331024", town_codes="",
         cover_desc="以神仙居景区为核心的环神仙居精品片区组团", scale_villages="",
         founded_ymd="2025", founded_precision="year", status="运行中", lead_org="",
         issuer="仙居县文广旅体局",
         summary="仙居四大精品片区组团之一「环神仙居精品片区」，以神仙居景区（国家5A级）为核心。2025年以来仙居推进四大精品片区组团发展，覆盖10个乡镇25个重点村。省320名单归属待核。",
         first_source_id="S095"),
    dict(area_id="A330376", name="万年文化精品片区", name_norm="万年文化精品片区", type_code="T05",
         type_primary_note="仙居四大精品片区组团之一", tags="精品片区;下汤遗址;文化;仙居",
         city_code="331000", county_code="331024", town_codes="横溪镇",
         cover_desc="以万年下汤遗址为核心的文化精品片区组团", scale_villages="",
         founded_ymd="2025", founded_precision="year", status="运行中", lead_org="",
         issuer="仙居县文广旅体局",
         summary="仙居四大精品片区组团之一「万年文化精品片区」，以下汤遗址为核心。横溪镇上江垟村毗邻下汤遗址，盘活古建筑开设研学工坊打造非遗特色村。省320名单归属待核。",
         first_source_id="S095"),
    dict(area_id="A330377", name="高铁滨溪精品片区", name_norm="高铁滨溪精品片区", type_code="T05",
         type_primary_note="仙居四大精品片区组团之一", tags="精品片区;高铁;滨溪;仙居",
         city_code="331000", county_code="331024", town_codes="",
         cover_desc="以永安溪和高铁站为轴线的滨溪精品片区组团", scale_villages="",
         founded_ymd="2025", founded_precision="year", status="运行中", lead_org="",
         issuer="仙居县文广旅体局",
         summary="仙居四大精品片区组团之一「高铁滨溪精品片区」，以永安溪、高铁站为轴线。省320名单归属待核。",
         first_source_id="S095"),
    dict(area_id="A330378", name="东部运动精品片区", name_norm="东部运动精品片区", type_code="T05",
         type_primary_note="仙居四大精品片区组团之一", tags="精品片区;运动;321省道;仙居",
         city_code="331000", county_code="331024", town_codes="白塔镇;上张乡;朱溪镇",
         cover_desc="以321省道为主轴联动白塔、上张、朱溪等乡镇", scale_villages="",
         founded_ymd="2025", founded_precision="year", status="运行中", lead_org="",
         issuer="仙居县文广旅体局",
         summary="仙居四大精品片区组团之一「东部运动精品片区」，以321省道为主轴串珠成链，联动白塔、上张、朱溪等乡镇，聚焦户外运动与体育赛事。朱溪镇杨丰山村建设运动驿站、智慧跑道、云上美术馆。省320名单归属待核。",
         first_source_id="S095"),
    # Ningbo
    dict(area_id="A330379", name="雪窦乡履片区", name_norm="雪窦乡履片区", type_code="T05",
         type_primary_note="奉化重点村组团片区东山村为重点村", tags="重点村组团;民宿;雪窦山;奉化",
         city_code="330200", county_code="330213", town_codes="",
         cover_desc="以东山村为重点村的雪窦乡履片区", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="运行中", lead_org="",
         issuer="宁波市农业农村局",
         summary="奉化雪窦乡履片区以东山村为重点村，引入专业运营团队盘活闲置农房60余栋，建成民宿28家，带动村集体增收60万元、农户增收450万元。东山村打造「一览咖啡」「花庭·东山上」等业态，为省级现场会考察点。片区全称「雪窦乡履」或「雪窦乡」待核。",
         first_source_id="S088"),
    dict(area_id="A330380", name="金溪五村片区", name_norm="金溪五村片区", type_code="T05",
         type_primary_note="奉化青年入乡133机制片区", tags="重点村组团;青年入乡;奉化",
         city_code="330200", county_code="330213", town_codes="",
         cover_desc="以蒋家池头村为考察点的金溪五村片区", scale_villages="5",
         founded_ymd="", founded_precision="unknown", status="运行中", lead_org="",
         issuer="宁波市农业农村局",
         summary="奉化金溪五村片区以蒋家池头村为省级现场会考察点，有「133」青年入乡机制，提供5年最高400万元引育奖补和最高300万元创业免息贷款。省320名单归属待核。",
         first_source_id="S088"),
    dict(area_id="A330381", name="翠屏梅堰片区", name_norm="翠屏梅堰片区", type_code="T04",
         type_primary_note="慈溪杨梅共富工坊联盟产业片区", tags="重点村组团;杨梅;共富工坊;慈溪",
         city_code="330200", county_code="330282", town_codes="",
         cover_desc="慈溪翠屏梅堰片区杨梅产业", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="运行中", lead_org="",
         issuer="宁波市农业农村局",
         summary="慈溪翠屏梅堰片区组建杨梅共富工坊联盟，带动1500户梅农户均年增收超1万元。为2026年省深化乡村片区组团发展现场会交流发言点名片区。省320名单归属待核。",
         first_source_id="S088"),
    dict(area_id="A330382", name="云湖片区", name_norm="云湖片区", type_code="T05",
         type_primary_note="江北片区IP云湖生活", tags="重点村组团;片区IP;江北",
         city_code="330200", county_code="330205", town_codes="",
         cover_desc="江北云湖片区整体运营", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="运行中", lead_org="",
         issuer="宁波市农业农村局",
         summary="江北云湖片区整体运营后4个薄弱村收入实现翻三倍，形成「云湖生活」全国瞩目片区IP。省320名单归属待核。",
         first_source_id="S088"),
    # Jinhua
    dict(area_id="A330383", name="产教共融研旅花园片区", name_norm="产教共融研旅花园片区", type_code="T05",
         type_primary_note="2026第一批省级重点村对应片区", tags="省级重点村;产教融合;研学;东阳",
         city_code="330700", county_code="330783", town_codes="南马镇",
         cover_desc="花园村为重点村串联上安恬、下安恬、泉府、下格、联合、紫溪、大联、梨枫、山联等9村",
         scale_villages="10", founded_ymd="2026-01-01", founded_precision="year", status="运行中",
         lead_org="东阳市农业农村局", issuer="浙江省农业农村厅",
         summary="2026年第一批省级重点村对应片区「产教共融·研旅花园片区」，以花园村为重点村，串联上安恬村、下安恬村、泉府村、下格村、联合村、紫溪村、大联村、梨枫村、山联村等周边9个行政村，打造「产教融合赋能、文旅双链驱动」特色共富片区组团。",
         first_source_id="S091"),
    dict(area_id="A330384", name="派溪童片区", name_norm="派溪童片区", type_code="T05",
         type_primary_note="入选省级重点村片区", tags="省级重点村;婺美共富;汤溪;金华开发区",
         city_code="330700", county_code="330702", town_codes="汤溪镇",
         cover_desc="金华开发区汤溪镇派溪童片区", scale_villages="",
         founded_ymd="2025", founded_precision="year", status="运行中", lead_org="",
         issuer="金华开发区",
         summary="金华开发区「婺美共富」发展轴和美乡村组团片区中，派溪童片区入选省级重点村片区。2025年第二批省级重点村（非山区海岛县）对应汤溪镇派溪童村。片区辐射带动周边村协同发展。",
         first_source_id="S093"),
    # Shaoxing
    dict(area_id="A330385", name="酒香有戏片区", name_norm="酒香有戏片区", type_code="T05",
         type_primary_note="2026第一批省级重点村对应片区", tags="省级重点村;酒文化;戏曲;越城",
         city_code="330600", county_code="330602", town_codes="东浦街道",
         cover_desc="南村村为重点村联同东浦村、王城寺村、壶觞村等",
         scale_villages="4", founded_ymd="2026-01-01", founded_precision="year", status="运行中",
         lead_org="绍兴市农业农村局", issuer="浙江省农业农村厅",
         summary="2026年第一批省级重点村对应片区「酒香有戏」片区，越城区东浦街道南村村深耕酒文化与戏曲底蕴，联同东浦村、王城寺村、壶觞村等村打造。省320名单2026第一批确认。",
         first_source_id="S092"),
    dict(area_id="A330386", name="踏雪寻梅生态文旅片区", name_norm="踏雪寻梅生态文旅片区", type_code="T05",
         type_primary_note="2026第一批省级重点村对应片区", tags="省级重点村;梅花;生态文旅;柯桥",
         city_code="330600", county_code="330603", town_codes="王坛镇",
         cover_desc="东村村为重点村联同王城村、丹家村等",
         scale_villages="3", founded_ymd="2026-01-01", founded_precision="year", status="运行中",
         lead_org="绍兴市农业农村局", issuer="浙江省农业农村厅",
         summary="2026年第一批省级重点村对应片区「踏雪寻梅」生态文旅片区，柯桥区王坛镇东村村以梅花为媒，联同王城村、丹家村等村构建。省320名单2026第一批确认。",
         first_source_id="S092"),
    # Hangzhou
    dict(area_id="A330387", name="139乡宿片区", name_norm="139乡宿片区", type_code="T05",
         type_primary_note="建德航头镇乡宿驱动片区组团", tags="片区组团;乡宿;农文旅;建德",
         city_code="330100", county_code="330182", town_codes="航头镇",
         cover_desc="以航川村139乡宿为核心联动周边五个行政村",
         scale_villages="6", founded_ymd="2026-01", founded_precision="month", status="运行中",
         lead_org="航头镇党委", issuer="杭州市农业农村局",
         summary="建德市航头镇「139乡宿」片区组团2026年1月启动建设，以航川村「139乡宿」为核心联动周边五个行政村，构建「一心」「两园」「多点」乡村振兴示范片区。成立「139乡宿」产业大党委，「139乡宿」经营模式已在3县7镇15村复制落地。省320名单归属待核。",
         first_source_id="S094"),
    dict(area_id="A330388", name="龙门秘境片区", name_norm="龙门秘境片区", type_code="T05",
         type_primary_note="临安高虹镇三村统筹片区组团", tags="片区组团;古村;户外;临安",
         city_code="330100", county_code="330112", town_codes="高虹镇",
         cover_desc="石门村、龙上村、大山村三村统筹",
         scale_villages="3", founded_ymd="2017", founded_precision="year", status="运行中",
         lead_org="高虹镇", issuer="杭州市农业农村局",
         summary="临安区高虹镇石门村、龙上村、大山村2017年共同打造「龙门秘境」片区组团。石门村定位「古村寻韵+红色研学」、龙上村聚焦「奇石探险+户外畅玩」、大山村深耕「梯田康养+松林度假」。非临安发展轴十七组团名单，为镇级片区组团。省320名单归属待核。",
         first_source_id="S094"),
    # Jiaxing / Haining
    dict(area_id="A330389", name="大桃园片区", name_norm="大桃园片区", type_code="T05",
         type_primary_note="海宁盐官跨镇11村片区组团八大模式", tags="片区组团;跨镇;八大模式;海宁",
         city_code="330400", county_code="330481", town_codes="盐官镇",
         cover_desc="桃园村跨镇联动周边11个村",
         scale_villages="12", founded_ymd="", founded_precision="unknown", status="运行中",
         lead_org="桃园村党委", issuer="海宁市人民政府",
         summary="海宁市盐官镇桃园村「大桃园」乡村片区组团发展模式跨镇联动周边11个村，拓展「培训+研学+文创+旅游」业态，打造花卉、稻米、果蔬3大亿元产业。大桃园组团机制入选省乡村片区组团发展「八大模式」典型案例。省320名单归属待核。",
         first_source_id="S096"),
    dict(area_id="A330390", name="大博儒桥片区", name_norm="大博儒桥片区", type_code="T05",
         type_primary_note="海宁周王庙乡村振兴片区组团", tags="片区组团;众筹公园;海宁",
         city_code="330400", county_code="330481", town_codes="周王庙镇",
         cover_desc="博儒桥村（重点村）带动上林村、长春村、星火村等",
         scale_villages="4", founded_ymd="", founded_precision="unknown", status="运行中",
         lead_org="博儒桥村党委", issuer="海宁市人民政府",
         summary="海宁市周王庙镇「大博儒桥」乡村振兴片区组团，以博儒桥村为重点村带动上林村、长春村、星火村、云龙村等。博儒桥村以19个众筹精品公园闻名。海宁十大片区组团「八大模式」之一。省320名单归属待核。",
         first_source_id="S099"),
    dict(area_id="A330391", name="潮起尖山片区", name_norm="潮起尖山片区", type_code="T05",
         type_primary_note="海宁黄湾尖山村为重点村组团片区", tags="片区组团;潮文化;运动;海宁",
         city_code="330400", county_code="330481", town_codes="黄湾镇",
         cover_desc="以尖山村为重点村联合周边多个行政村规划47.5平方公里",
         scale_villages="", founded_ymd="", founded_precision="unknown", status="运行中",
         lead_org="", issuer="海宁市人民政府",
         summary="海宁市黄湾镇以尖山村为重点村联合周边多个行政村组建「潮起尖山」组团片区，规划总面积47.5平方公里，串联「自然潮、农业潮、运动潮、乡村潮」四大特色主题。与「大尖山乡村振兴片区组团」疑为同一单元。省320名单归属待核。",
         first_source_id="S097"),
    dict(area_id="A330392", name="神仙湖片区", name_norm="神仙湖片区", type_code="T05",
         type_primary_note="入选省农村综合性改革试点片区组团", tags="片区组团;农村综改;海宁",
         city_code="330400", county_code="330481", town_codes="",
         cover_desc="海宁神仙湖片区组团", scale_villages="",
         founded_ymd="", founded_precision="unknown", status="待核", lead_org="",
         issuer="海宁市人民政府",
         summary="「神仙湖」片区组团入选省农村综合性改革试点。海宁市2025年国民经济和社会发展计划执行情况报告确认。省320名单归属待核。",
         first_source_id="S098"),
]

# ── sources ────────────────────────────────────────────────────────────────
SOURCES = [
    dict(source_id="S087", area_id="A330368", url=RAW_DIRS["20260909-tz-pianqu-zutuan"]["url"],
         title=RAW_DIRS["20260909-tz-pianqu-zutuan"]["title"],
         publisher=RAW_DIRS["20260909-tz-pianqu-zutuan"]["publisher"],
         published_ymd="2026-09-09", excerpt=RAW_DIRS["20260909-tz-pianqu-zutuan"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20260909-tz-pianqu-zutuan/原文.md"),
    dict(source_id="S088", area_id="A330379", url=RAW_DIRS["20260509-nb-xianchanghui"]["url"],
         title=RAW_DIRS["20260509-nb-xianchanghui"]["title"],
         publisher=RAW_DIRS["20260509-nb-xianchanghui"]["publisher"],
         published_ymd="2026-05-09", excerpt=RAW_DIRS["20260509-nb-xianchanghui"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20260509-nb-xianchanghui/原文.md"),
    dict(source_id="S089", area_id="A330379", url=RAW_DIRS["20260509-zjol-xueyushi"]["url"],
         title=RAW_DIRS["20260509-zjol-xueyushi"]["title"],
         publisher=RAW_DIRS["20260509-zjol-xueyushi"]["publisher"],
         published_ymd="2026-05-09", excerpt=RAW_DIRS["20260509-zjol-xueyushi"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20260509-zjol-xueyushi/原文.md"),
    dict(source_id="S090", area_id="A330383", url=RAW_DIRS["20260423-jh-10-shengjidiancun"]["url"],
         title=RAW_DIRS["20260423-jh-10-shengjidiancun"]["title"],
         publisher=RAW_DIRS["20260423-jh-10-shengjidiancun"]["publisher"],
         published_ymd="2026-04-23", excerpt=RAW_DIRS["20260423-jh-10-shengjidiancun"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20260423-jh-10-shengjidiancun/原文.md"),
    dict(source_id="S091", area_id="A330383", url=RAW_DIRS["20260506-hy-huayuan-pianqu"]["url"],
         title=RAW_DIRS["20260506-hy-huayuan-pianqu"]["title"],
         publisher=RAW_DIRS["20260506-hy-huayuan-pianqu"]["publisher"],
         published_ymd="2026-05-06", excerpt=RAW_DIRS["20260506-hy-huayuan-pianqu"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20260506-hy-huayuan-pianqu/原文.md"),
    dict(source_id="S092", area_id="A330385", url=RAW_DIRS["20260419-sx-6-cun"]["url"],
         title=RAW_DIRS["20260419-sx-6-cun"]["title"],
         publisher=RAW_DIRS["20260419-sx-6-cun"]["publisher"],
         published_ymd="2026-04-19", excerpt=RAW_DIRS["20260419-sx-6-cun"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20260419-sx-6-cun/原文.md"),
    dict(source_id="S093", area_id="A330384", url=RAW_DIRS["20260102-jhkq-paixitong"]["url"],
         title=RAW_DIRS["20260102-jhkq-paixitong"]["title"],
         publisher=RAW_DIRS["20260102-jhkq-paixitong"]["publisher"],
         published_ymd="2026-01-02", excerpt=RAW_DIRS["20260102-jhkq-paixitong"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20260102-jhkq-paixitong/原文.md"),
    dict(source_id="S094", area_id="A330387", url=RAW_DIRS["20260120-hz-pianqu-zutuan"]["url"],
         title=RAW_DIRS["20260120-hz-pianqu-zutuan"]["title"],
         publisher=RAW_DIRS["20260120-hz-pianqu-zutuan"]["publisher"],
         published_ymd="2026-01-20", excerpt=RAW_DIRS["20260120-hz-pianqu-zutuan"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20260120-hz-pianqu-zutuan/原文.md"),
    dict(source_id="S095", area_id="A330375", url=RAW_DIRS["20260202-xj-sida-jingpin"]["url"],
         title=RAW_DIRS["20260202-xj-sida-jingpin"]["title"],
         publisher=RAW_DIRS["20260202-xj-sida-jingpin"]["publisher"],
         published_ymd="2026-02-02", excerpt=RAW_DIRS["20260202-xj-sida-jingpin"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20260202-xj-sida-jingpin/原文.md"),
    dict(source_id="S096", area_id="A330389", url=RAW_DIRS["20250619-hn-dayuan"]["url"],
         title=RAW_DIRS["20250619-hn-dayuan"]["title"],
         publisher=RAW_DIRS["20250619-hn-dayuan"]["publisher"],
         published_ymd="2025-06-19", excerpt=RAW_DIRS["20250619-hn-dayuan"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20250619-hn-dayuan/原文.md"),
    dict(source_id="S097", area_id="A330391", url=RAW_DIRS["20260416-hn-chaoshan"]["url"],
         title=RAW_DIRS["20260416-hn-chaoshan"]["title"],
         publisher=RAW_DIRS["20260416-hn-chaoshan"]["publisher"],
         published_ymd="2026-04-16", excerpt=RAW_DIRS["20260416-hn-chaoshan"]["excerpt"][:200],
         fetched_at=NOW, credibility="A",
         local_path="data/raw/330000-浙江/20260416-hn-chaoshan/原文.md"),
    dict(source_id="S098", area_id="A330392", url="https://www.hnsrd.gov.cn/home/docDetail.html?id=16850",
         title="关于海宁市2025年国民经济和社会发展计划执行情况及2026年计划草案的报告",
         publisher="海宁市人大常委会", published_ymd="2026-02-03",
         excerpt="「神仙湖」片区组团入选省农村综合性改革试点，大桃园组团机制入选省乡村片区组团发展「八大模式」典型案例，翁埠夜市入选省首批重点培育共富市集。",
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20251119-hn-shida-pianqu/原文.md"),
    dict(source_id="S099", area_id="A330390", url=RAW_DIRS["20251119-hn-shida-pianqu"]["url"],
         title=RAW_DIRS["20251119-hn-shida-pianqu"]["title"],
         publisher=RAW_DIRS["20251119-hn-shida-pianqu"]["publisher"],
         published_ymd="2025-11-19", excerpt=RAW_DIRS["20251119-hn-shida-pianqu"]["excerpt"][:200],
         fetched_at=NOW, credibility="B",
         local_path="data/raw/330000-浙江/20251119-hn-shida-pianqu/原文.md"),
]

# ── area_source_map ────────────────────────────────────────────────────────
MAPS = []
# S087 supports all Taizhou areas
for aid in ["A330368","A330369","A330370","A330371","A330372","A330373","A330374"]:
    MAPS.append(dict(area_id=aid, source_id="S087", entity_type="area",
                     rel="primary" if aid=="A330368" else "support"))
# S088 supports Ningbo areas
for aid in ["A330379","A330380","A330381","A330382"]:
    MAPS.append(dict(area_id=aid, source_id="S088", entity_type="area",
                     rel="primary" if aid=="A330379" else "support"))
# S089 support for 雪窦/金溪
MAPS.append(dict(area_id="A330379", source_id="S089", entity_type="area", rel="support"))
MAPS.append(dict(area_id="A330380", source_id="S089", entity_type="area", rel="support"))
# S090 Jinhua 10 villages - primary for 花园 (via S091), support for others
MAPS.append(dict(area_id="A330383", source_id="S090", entity_type="area", rel="support"))
MAPS.append(dict(area_id="A330384", source_id="S090", entity_type="area", rel="support"))
# S091 花园 primary
MAPS.append(dict(area_id="A330383", source_id="S091", entity_type="area", rel="primary"))
# S092 Shaoxing
MAPS.append(dict(area_id="A330385", source_id="S092", entity_type="area", rel="primary"))
MAPS.append(dict(area_id="A330386", source_id="S092", entity_type="area", rel="support"))
# S093 派溪童
MAPS.append(dict(area_id="A330384", source_id="S093", entity_type="area", rel="primary"))
# S094 Hangzhou
MAPS.append(dict(area_id="A330387", source_id="S094", entity_type="area", rel="primary"))
MAPS.append(dict(area_id="A330388", source_id="S094", entity_type="area", rel="support"))
# S095 Xianju
for aid in ["A330375","A330376","A330377","A330378"]:
    MAPS.append(dict(area_id=aid, source_id="S095", entity_type="area",
                     rel="primary" if aid=="A330375" else "support"))
# S096 大桃园
MAPS.append(dict(area_id="A330389", source_id="S096", entity_type="area", rel="primary"))
# S097 潮起尖山
MAPS.append(dict(area_id="A330391", source_id="S097", entity_type="area", rel="primary"))
# S098 神仙湖 + 大桃园 support
MAPS.append(dict(area_id="A330392", source_id="S098", entity_type="area", rel="primary"))
MAPS.append(dict(area_id="A330389", source_id="S098", entity_type="area", rel="support"))
# S099 大博儒桥
MAPS.append(dict(area_id="A330390", source_id="S099", entity_type="area", rel="primary"))
# A330160 support from S087
MAPS.append(dict(area_id="A330160", source_id="S087", entity_type="area", rel="support"))

# ── area_region_map ────────────────────────────────────────────────────────
COUNTY_NAME = {
    "331023":"天台县","331082":"临海市","331002":"椒江区","331003":"黄岩区",
    "331022":"三门县","331081":"玉环市","331024":"仙居县","330213":"奉化区",
    "330282":"慈溪市","330205":"江北区","330783":"东阳市","330702":"婺城区",
    "330602":"越城区","330603":"柯桥区","330182":"建德市","330112":"临安区",
    "330481":"海宁市","330781":"兰溪市",
}
TOWN_NAME = {
    "赤城街道":"赤城街道","街头镇":"街头镇","龙溪乡":"龙溪乡","江南街道":"江南街道",
    "大陈镇":"大陈镇","屿头乡":"屿头乡","亭旁镇":"亭旁镇","干江镇":"干江镇",
    "白塔镇":"白塔镇","上张乡":"上张乡","朱溪镇":"朱溪镇","横溪镇":"横溪镇",
    "南马镇":"南马镇","汤溪镇":"汤溪镇","东浦街道":"东浦街道","王坛镇":"王坛镇",
    "航头镇":"航头镇","高虹镇":"高虹镇","盐官镇":"盐官镇","周王庙镇":"周王庙镇",
    "黄湾镇":"黄湾镇",
}
REGS = []
for a in AREAS:
    aid = a["area_id"]
    cc = a["county_code"]
    REGS.append(dict(area_id=aid, level="county", region_code=cc,
                     region_name=COUNTY_NAME.get(cc, cc)))
    for t in (a.get("town_codes") or "").split(";"):
        t = t.strip()
        if t:
            REGS.append(dict(area_id=aid, level="town", region_code=t,
                             region_name=TOWN_NAME.get(t, t)))


def append_csv(path, fields, rows, has_header_check):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  appended {len(rows)} rows -> {path}")


def main():
    # 1. raw snapshots
    for dname, meta in RAW_DIRS.items():
        d = os.path.join(RAW, dname)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "原文.md"), "w", encoding="utf-8") as f:
            f.write(f"# {meta['title']}\n\n")
            f.write(f"- URL: {meta['url']}\n")
            f.write(f"- 发布者: {meta['publisher']}\n")
            f.write(f"- 发布日期: {meta['published_ymd']}\n")
            f.write(f"- 抓取日期: {NOW}\n")
            f.write(f"- cred: {meta['credibility']}\n\n")
            f.write("## 摘录\n\n")
            f.write(meta["excerpt"] + "\n")
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({
                "url": meta["url"], "title": meta["title"],
                "publisher": meta["publisher"], "published_ymd": meta["published_ymd"],
                "fetched_at": NOW, "credibility": meta["credibility"],
            }, f, ensure_ascii=False, indent=2)
    print(f"  wrote {len(RAW_DIRS)} raw snapshot dirs")

    # 2. fill area timestamps
    for a in AREAS:
        a.setdefault("province_code", "330000")
        a.setdefault("record_state", "active")
        a["created_at"] = NOW
        a["updated_at"] = NOW
        a["created_by"] = CB
        # ensure all AREA_FIELDS present
        for k in AREA_FIELDS:
            a.setdefault(k, "")

    # 3. source timestamps
    for s in SOURCES:
        s["fetched_at"] = NOW
        s.setdefault("hash_sha256", "")
        for k in SRC_FIELDS:
            s.setdefault(k, "")

    # 4. append
    append_csv(os.path.join(BP, "ZJ-area.csv"), AREA_FIELDS, AREAS, True)
    append_csv(os.path.join(BP, "ZJ-source.csv"), SRC_FIELDS, SOURCES, True)
    append_csv(os.path.join(BP, "ZJ-area_source_map.csv"), MAP_FIELDS, MAPS, True)
    append_csv(os.path.join(BP, "ZJ-area_region_map.csv"), REG_FIELDS, REGS, True)

    print(f"\nDone: {len(AREAS)} areas, {len(SOURCES)} sources, {len(MAPS)} maps, {len(REGS)} regs")


if __name__ == "__main__":
    main()
