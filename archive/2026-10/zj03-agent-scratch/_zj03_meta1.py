# -*- coding: utf-8 -*-
"""把已抓取的正文与人工核定的元数据组装成 POL-ZJ03-policy.jsonl（追加写入）。
用法: python _zj03_emit.py <part:1|2|3>
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
TXT = D + r"\_zj03_raw\txt"
OUT = r"D:\CODEX\全国乡村片区化数据库\data\stage\POL-ZJ03-policy.jsonl"
FETCHED = "2026-11-05"

DROP = re.compile(r"^(打印|关闭|打印 关闭|【返回顶部】.*|【打印本稿】.*|字体：\[ 大 中 小 \]|"
                  r"浏览次数：.*|网站首页 >|扫一扫.*|分享到.*|-)$")


def clean(md):
    lines = []
    for l in md.split("\n"):
        s = l.strip()
        if DROP.match(s):
            continue
        if s.startswith("网站首页") and ">" in s:
            continue
        lines.append(s)
    # 去重长行（政府网常见的重复模块）
    seen, out = set(), []
    for l in lines:
        key = l.strip()
        if len(key) > 25:
            if key in seen:
                continue
            seen.add(key)
        out.append(l)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt


def body(_id):
    p = os.path.join(TXT, _id + ".json")
    d = json.load(open(p, encoding="utf-8"))
    return clean(d["body_md"]), d["title"], d["url"]


META = [
 # ---------------- 宁波市海曙区 ----------------
 dict(id="HS01", title="《海曙区“县城—中心镇—重点村”发展轴空间专项规划（2025-2035年）》正式发布",
      doc_no="", issuer="宁波市自然资源和规划局海曙分局", issuer_level="county",
      issued_ymd="2026-01-27", published_ymd="2026-01-27", doc_type="动态", source_kind="部门动态",
      province_code="330000", city_code="330200", county_code="330203",
      instruments="规划,发展轴,重点村组团片区,强城兴村融合,国土空间",
      scope_desc="规划范围分全域研究范围与发展轴空间范围，发展轴空间约407.38平方公里，覆盖高桥、石碶、集士港、古林、横街、鄞江、章水、龙观等乡镇（街道）；构建“一轴双心、四镇六片”体系",
      target_areas=6, budget_wan="", valid_state="现行有效", credibility="B",
      summary="海曙区“县城—中心镇—重点村”发展轴空间专项规划于2026年1月15日经宁波市人民政府批复后正式发布实施，规划期2025—2035年、近期至2027年。发展轴空间范围约407.38平方公里，覆盖高桥镇、石碶街道、集士港镇、古林镇、横街镇、鄞江镇、章水镇、龙观乡等。总体定位“科创人文、四明新韵”，构建“一轴双心、四镇六片”空间体系：“一轴”以月塘东至章水镇为主轴并辅三条次轴，“双心”为月塘东与枢纽南门户区，“四镇”为古林、集士港、横街、鄞江四个中心镇，“六片”为深溪、茂新、它山堰等重点村组团片区。",
      slug="zj-nb-hs-fazhanzhou-zhuanxiangguihua-fabu", areas=[], events=[]),
 dict(id="HS03", title="海曙区“县城—中心镇—重点村”发展轴空间专项规划批前公示",
      doc_no="", issuer="宁波市自然资源和规划局海曙分局", issuer_level="county",
      issued_ymd="2025-09-16", published_ymd="2025-09-16", doc_type="公告", source_kind="政策文件",
      province_code="330000", city_code="330200", county_code="330203",
      instruments="规划,发展轴,重点村,强城兴村融合,国土空间,公众参与",
      scope_desc="规划范围为海曙区行政辖区595.19平方公里；期限2025—2035年，近期到2027年；公示期2025年9月17日至10月17日",
      target_areas="", budget_wan="", valid_state="未知", credibility="A",
      summary="海曙分局就发展轴空间专项规划征求意见稿公开征求意见，公示期2025年9月17日至10月17日。文件载明编制依据为2025年省委、市委一号文件关于围绕“强城”“兴村”“融合”建强“县城—中心镇—重点村”发展轴的要求，以及省委农办、省自然资源厅、省住建厅、省农业农村厅印发的相关通知。规划范围595.19平方公里，期限2025—2035年、近期到2027年；定位为“智汇广德、古韵南塘”科创人文共富共美发展轴，空间体系为“一轴双心、四镇六片”，并设2027年、2035年分段目标。",
      slug="zj-nb-hs-fazhanzhou-guihua-piqiangongshi", areas=[], events=[]),
 dict(id="HS02", title="海曙大雷村，省级重点村",
      doc_no="", issuer="宁波市海曙区农业农村局", issuer_level="county",
      issued_ymd="", published_ymd="2026-04-29", doc_type="动态", source_kind="部门动态",
      province_code="330000", city_code="330200", county_code="330203",
      instruments="重点村组团片区,片区化,产业,品牌,农文旅,强村带弱村",
      scope_desc="横街镇大雷村入选2026年度第一批省级重点村，牵头“浙东竹海组团”，带动竹丝岚、云洲、凤凰、上阵、半山、爱岭、爱中、芝岭、毛岙等9个周边村",
      target_areas=1, budget_wan="", valid_state="现行有效", credibility="B",
      summary="浙江省农业农村厅公布2026年度第一批省级重点村名单，海曙区横街镇大雷村入选，由其牵头的“浙东竹海组团”纳入省级重点建设序列。片区以大雷村为主引擎，带动竹丝岚村、云洲村、凤凰村、上阵村、半山村、爱岭村、爱中村、芝岭村、毛岙村等周边村协同提升。横街镇拥有5.7万亩竹林，依托宁波浙东大竹海景区开发有限公司形成“浙东竹海片区”，并提出以“五竹共富”（竹笋、竹山、竹子、竹海、竹空气）为抓手，实现“一村带一片、一片兴全域”。",
      slug="zj-nb-hs-daleicun-shengjizhongdiancun", areas=[], events=[]),
 # ---------------- 宁波市北仑区 ----------------
 dict(id="BL01", title="《北仑区“县城-中心镇-重点村”发展轴空间专项规划（2025-2035年）》批后公布",
      doc_no="", issuer="宁波市自然资源和规划局北仑分局", issuer_level="county",
      issued_ymd="2025-12-31", published_ymd="2025-12-31", doc_type="公告", source_kind="政策文件",
      province_code="330000", city_code="330200", county_code="330206",
      instruments="规划,发展轴,重点村组团片区,强城兴村融合,国土空间",
      scope_desc="研究范围为北仑区全域，重点范围为“科创策源·智荟浃江发展轴”轴域；期限2025—2035年、近期至2027年；形成“一主城、两中心、九组团”县域发展轴城镇村体系",
      target_areas=9, budget_wan="", valid_state="现行有效", credibility="A",
      summary="规划已经宁波市人民政府批复同意，按《浙江省国土空间规划条例》公布主要内容。研究范围为北仑全域，重点范围为“科创策源·智荟浃江发展轴”轴域，期限2025—2035年、近期至2027年。总体目标“多元融合·城乡共荣”，空间体系为“一核强区引领、两轴共富带动”，即北仑主城区为核心，科创策源·智荟浃江发展轴与滨海蓝湾发展轴为两轴；城镇村体系为“一主城、两中心、九组团”，九组团即以合兴村、城湾村、河头村、三山村、永久村、下阳村、福民村、梅港村、嘉溪村为重点村的村庄片区组团。",
      slug="zj-nb-bl-fazhanzhou-zhuanxiangguihua-pihou", areas=[], events=[]),
 dict(id="BL02", title="王程专题调研片区组团发展工作",
      doc_no="", issuer="宁波市北仑区大碶街道", issuer_level="town",
      issued_ymd="2026-08-19", published_ymd="2026-08-26", doc_type="动态", source_kind="部门动态",
      province_code="330000", city_code="330200", county_code="330206",
      instruments="片区组团,三区联动,青年入乡,乡村运营,片区组团,一片一策,人才,产业",
      scope_desc="区委书记王程调研大灵峰片区、九峰山农创逸居片区；九峰山农创逸居片区涵盖城湾、和鸽等6个行政村",
      target_areas="", budget_wan="", valid_state="现行有效", credibility="B",
      summary="2026年8月19日北仑区委书记王程专题调研片区组团发展工作，强调以“千万工程”牵引城乡融合、统筹“强城”“兴村”“融合”三篇文章。大灵峰片区是北仑探索产业园区、工业社区、农村片区“三区”联动模式的重点示范样板，在嘉溪村乌石岙考察青年社群、村民会客厅、融合餐饮等场景。九峰山农创逸居片区涵盖城湾、和鸽等6个行政村，打造“创客赋能、场景消费、产业焕活”三位一体模式，以“一张闲置资源地图、一张政策清单、一个创业阵地、一支服务队伍”为青创客赋能。要求“一片一策”优化公共服务布局和要素资源配置，协同推进片区组团、乡村运营与青年入乡。",
      slug="zj-nb-bl-pianquzutuan-diaoyan-wangcheng",
      areas=[{"area_id": "A330046", "entity_type": "area", "rel": "support"}], events=[]),
 dict(id="BL03", title="北仑区召开第二批重点村组团片区遴选暨乡村运营互学互促交流会",
      doc_no="", issuer="宁波市北仑区农业农村局", issuer_level="county",
      issued_ymd="2026-05-22", published_ymd="2026-05-22", doc_type="动态", source_kind="部门动态",
      province_code="330000", city_code="330200", county_code="330206",
      instruments="遴选,片区组团,乡村运营,三区联动,考核,七个强化,强城兴村融合",
      scope_desc="交流大灵峰片区、海上梅山片区经验；新碶、柴桥、春晓、白峰四个街道汇报第二批重点村组团片区建设方案",
      target_areas="", budget_wan="", valid_state="现行有效", credibility="B",
      summary="2026年5月22日北仑区在柴桥街道花农会客厅召开第二批重点村组团片区遴选暨乡村运营互学互促交流会。大碶街道大灵峰片区、梅山街道海上梅山片区交流项目谋划与运营经验；新碶、柴桥、春晓、白峰四个街道汇报第二批片区建设方案并逐一点评。区农业农村局局长张志龙指出，2025年以来省委将乡村片区组团发展作为“兴村”关键抓手，北仑“三区联动”组团路径以工业社区为桥梁、产业为纽带，已获《农民日报》报道及省市领导批示，并成功申报两批省级重点村片区组团；下一步紧扣“分类施策、有序发展、富民增收”，落实“七个强化”。",
      slug="zj-nb-bl-dierpizhongdiancun-linxuan", areas=[], events=[]),
 dict(id="BL04", title="白峰“片区组团”走出新路径",
      doc_no="", issuer="宁波市北仑区人民政府", issuer_level="county",
      issued_ymd="", published_ymd="2025-11-26", doc_type="动态", source_kind="新闻发布",
      province_code="330000", city_code="330200", county_code="330206",
      instruments="片区组团,党建联建,共富小组,企业投资+专业运营,强村公司,品牌,农文旅",
      scope_desc="白峰街道上阳片区覆盖上阳、下阳、阳东、勤山等6个行政村，以上阳山海田园片区为运营载体",
      target_areas="", budget_wan="", valid_state="现行有效", credibility="B",
      summary="报道北仑白峰街道上阳片区“片区组团”实践：覆盖上阳、下阳、阳东、勤山等6个行政村，街道党工委牵头联合区级职能部门与国企成立“峰上农旅”共富小组，全域推进“企业投资+专业运营”模式盘活闲置资源。片区以“虾㢀年糕”非遗品牌为抓手，连续11年举办年糕文旅集市，建成年糕非遗记忆馆和文化体验馆，并依托阳东田园综合体延伸农业生产、农事体验、教育科普等产业链。",
      slug="zj-nb-bl-baifeng-pianquzutuan-xinlujing", areas=[], events=[]),
 # ---------------- 宁波市鄞州区 ----------------
 dict(id="YZ01", title="《鄞州区“县城-中心镇-重点村”发展轴空间专项规划（2025-2035）》批后公布",
      doc_no="甬政发〔2025〕86号", issuer="宁波市自然资源和规划局鄞州分局", issuer_level="county",
      issued_ymd="2025-11-26", published_ymd="2025-12-22", doc_type="公告", source_kind="政策文件",
      province_code="330000", city_code="330200", county_code="330212",
      instruments="规划,发展轴,重点村组团片区,强城兴村融合,乡村振兴片区组团,产业,国土空间",
      scope_desc="鄞州区行政辖区陆域空间；期限2025—2035年、近期至2027年；近期形成“一城七镇八片区”，远期“一城两轴三镇十片区”",
      target_areas=8, budget_wan="", valid_state="现行有效", credibility="A",
      summary="《鄞州区“县城-中心镇-重点村”发展轴空间专项规划》于2025年11月26日获宁波市人民政府批复（甬政发〔2025〕86号），公布主要内容。规划期2025—2035年、近期至2027年。以“鄞南智汇山海发展轴”为定位，近期形成“一城七镇八片区”：一城为南部新城首南、下应街道；七镇含姜山、东钱湖两强镇与云龙、横溪、塘溪、咸祥、瞻岐五个特色镇；八片区为大湾底片区、种业创新片区、钱湖农文旅融合片区、禅意农旅片区、灵秀山水片区、红色人文片区、低空经济+片区、山海共富片区。远期建设北部“鄞北未来城乡示范发展轴”，形成“一城两轴三镇十片区”。",
      slug="zj-nb-yz-fazhanzhou-zhuanxiangguihua-pihou",
      areas=[{"area_id": "A330047", "entity_type": "area", "rel": "primary"},
             {"area_id": "A330048", "entity_type": "area", "rel": "mention"}],
      events=[{"area_id": "A330047", "entity_type": "area", "event_type": "批复",
               "ymd": "2025-11-26", "note": "甬政发〔2025〕86号批复，规划列“八片区”含大湾底片区"}]),
 dict(id="YZ02", title="我区新增2个省级重点村",
      doc_no="", issuer="宁波市鄞州区人民政府", issuer_level="county",
      issued_ymd="", published_ymd="2026-04-22", doc_type="动态", source_kind="新闻发布",
      province_code="330000", city_code="330200", county_code="330212",
      instruments="重点村组团片区,片区组团,产业,乡村运营,种业,农文旅,品牌IP",
      scope_desc="2026年第一批省级重点村全省94个村，鄞州2个：姜山镇东光村（稻香鄞南种业创新片区）、东吴镇天童村（东吴禅意农旅片区）；全区已有4个重点村（组团片区）列入省级名单，辐射带动周边34个村",
      target_areas=4, budget_wan="", valid_state="现行有效", credibility="B",
      summary="省农业农村厅公布2026年第一批省级重点村名单，全省94个村入选，鄞州区姜山镇东光村（稻香鄞南种业创新片区）与东吴镇天童村（东吴禅意农旅片区）上榜。稻香鄞南种业创新片区定位“种业硅谷 乐居鄞南”，由10个行政村组成，以东光村为重点村辐射9个村，面积约18.66平方公里；东吴禅意农旅片区以天童村为核心联结童一、三塘、勤勇3村并带动4个辐射村，面积约43.58平方公里。全区已有4个重点村（组团片区）列入省级名单，辐射带动34个村庄，累计培育乡村新业态105个。",
      slug="zj-nb-yz-xinzeng-shengjizhongdiancun", areas=[], events=[]),
 # ---------------- 温州市永嘉县 ----------------
 dict(id="YJ01", title="关于《永嘉县“县城-中心镇-重点村”发展轴空间专项规划（2025-2035年）》（草案）的公示",
      doc_no="", issuer="永嘉县自然资源和规划局", issuer_level="county",
      issued_ymd="2025-04-17", published_ymd="2025-04-17", doc_type="公告", source_kind="政策文件",
      province_code="330000", city_code="330300", county_code="330324",
      instruments="规划,发展轴,重点村,强城兴村融合,公众参与,先行县",
      scope_desc="永嘉县全域；公示期2025年4月17日至5月17日；永嘉为全省县域发展轴空间专项规划编制先行县",
      target_areas="", budget_wan="", valid_state="未知", credibility="A",
      summary="永嘉县自然资源和规划局公示县域发展轴空间专项规划草案，公示期2025年4月17日至5月17日。文件说明依据2025年省委一号文件关于以“千万工程”牵引城乡融合发展、缩小“三大差距”，统筹“强城”“兴村”“融合”，以县域为重要单元建强“县城—中心镇—重点村”发展轴的要求；永嘉作为全省县域发展轴空间专项规划编制先行县已完成规划编制。反馈渠道为电子邮箱与邮寄至县自然资源和规划局空间规划科。",
      slug="zj-wz-yj-fazhanzhou-guihua-caogangongshi", areas=[], events=[]),
 dict(id="YJ02", title="永嘉召开会议专题研究乡村片区组团发展和农业全产业链工作",
      doc_no="", issuer="永嘉县人民政府", issuer_level="county",
      issued_ymd="", published_ymd="2025-08-28", doc_type="动态", source_kind="新闻发布",
      province_code="330000", city_code="330300", county_code="330324",
      instruments="片区组团,组织,产业,规划,强城兴村融合,机制,青年乡创,农村改革",
      scope_desc="会议听取县发改局、县农业农村局汇报，桥头镇、桥下镇、岩头镇、枫林镇、云岭乡等单位汇报重点村组团片区工作推进情况",
      target_areas="", budget_wan="", valid_state="现行有效", credibility="B",
      summary="2025年8月26日永嘉县委书记吴呈钱主持召开会议，专题研究乡村片区组团发展和农业全产业链工作。会上县发改局汇报项目谋划情况，县农业农村局汇报片区组团与农业全产业链工作，桥头镇、桥下镇、岩头镇、枫林镇、云岭乡等汇报重点村组团片区推进情况。县委书记强调省委提出建强“县城—中心镇—重点村”发展轴，要突出“特色+产业”做优“土特产富”、“规划+计划”推进城乡一体谋划、“机制+制度”完善片区组团运行机制，选优配强村社班子、用好青年乡创平台，并以“小切口、大牵引”农村改革破题。",
      slug="zj-wz-yj-pianquzutuan-zhuanxianghuiyi",
      areas=[{"area_id": "A330165", "entity_type": "area", "rel": "support"},
             {"area_id": "A330166", "entity_type": "area", "rel": "support"},
             {"area_id": "A330167", "entity_type": "area", "rel": "support"},
             {"area_id": "A330168", "entity_type": "area", "rel": "support"},
             {"area_id": "A330169", "entity_type": "area", "rel": "support"}], events=[]),
]
