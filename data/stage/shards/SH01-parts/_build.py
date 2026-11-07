import json, re, sys
from pathlib import Path

ROOT = Path(r"D:\CODEX\全国乡村片区化数据库")
PARTS = ROOT / "data" / "stage" / "shards" / "SH01-parts"
TEXT = PARTS / "text"
OUT = ROOT / "data" / "stage" / "POL-SH01-policy.jsonl"
COUNTIES = ROOT / "data" / "stage" / "shards" / "SH01-counties.csv"

URLS = {
    "05": "https://www.pudong.gov.cn/zwgk/azt_zcfg/2026/168/356354.html",
    "06": "https://www.jiading.gov.cn/infopublicity/communique/publicinformationdetails/709",
    "07": "https://www.shanghai.gov.cn/nw12344/20250917/8873956951994f9aa013cf008cb5b5fd.html",
    "08": "https://www.shanghai.gov.cn/xcfz-gqwj13/20260803/819e262b6c1445a7b56fbe3a21eaa73e.html",
    "09": "https://www.shanghai.gov.cn/gwk/search/content/e2bf9d78-eb58-4e2f-89c7-9216e9723a9d",
}

META = {
    "05": dict(
        title="关于印发《浦东新区2026年乡村建设行动任务清单》的通知",
        doc_no="浦委农办〔2026〕4号",
        issuer="中共上海市浦东新区委员会农村工作领导小组办公室",
        county_code="310115", issued_ymd="2026-06-11", published_ymd="2026-06-17",
        doc_type="通知", instruments="土地,组织,考核,规划,人才,产业,数字",
        scope_desc="浦东新区各相关镇（含临港新片区范围）；清单含七大类40项任务，未点名具体片区",
        summary="浦东新区2026年乡村建设任务清单，依据农办乡建〔2026〕1号与沪委农办〔2026〕7号编制。第二部分专设“片区化推进宜居宜业和美乡村建设”，要求完成首批和美乡村试点建设任务、第三批试点总体建设进度达40%、和美乡村试点片区实现乡村一体化综合管护全覆盖；另设“加快推进设施片区建设”，要求每个设施片区至少储备1个高水平设施农业项目。规划端要求按需编制郊野地区规划、推进全域土地综合整治；考核端开展乡村振兴示范村发展评价；人才端推进乡村建筑师遴选与工匠年度培训；数字端推行“一村一码”与数字乡村标准化建设。",
        slug="pudong-2026-xiangcunjianshe-renwuqingdan", areas=[], events=[]),
    "06": dict(
        title="上海市嘉定区人民政府办公室关于印发《嘉定区推进乡村全面振兴“十五五”规划》的通知",
        doc_no="",
        issuer="上海市嘉定区人民政府办公室",
        county_code="310114", issued_ymd="2026-07-09", published_ymd="2026-07-09",
        doc_type="规划", instruments="财政,土地,组织,考核,规划,人才,产业",
        scope_desc="嘉定区全域（含娄塘镇/嘉定工业区）；设有“和美乡村片区覆盖村数量”指标，正文未点名具体片区名称",
        summary="嘉定区乡村全面振兴“十五五”规划。以片区化为载体，提出“推动和美乡村片区建设”，要求规划引领、由点及面、连片组团发展、打造示范片区，并探索引入社会资本参与片区规划设计建设运营；骨干指标中含“和美乡村片区覆盖村数量”。要素保障上提出整合涉农财政资金向集体经济重点领域倾斜、推进集体经营性建设用地入市扩面、发挥区委农村工作领导小组协调功能并实施挂图作战、形成可分解可监测可评估的工作指标压实责任。",
        slug="jiading-shiwuwu-guihua", areas=[], events=[]),
    "07": dict(
        title="崇明区人民政府关于印发崇明区促进新型农村集体经济高质量发展三年行动计划（2025—2027年）的通知",
        doc_no="沪崇府发〔2025〕31号",
        issuer="上海市崇明区人民政府",
        county_code="310151", issued_ymd="2025-09-03", published_ymd="2025-09-17",
        doc_type="方案", instruments="财政,土地,组织,考核,人才,金融,产业",
        scope_desc="崇明区全区涉农乡镇；将“五好两宜”和美乡村建设列为整合农村土地空间行动的措施，未点名具体片区",
        summary="崇明区促进新型农村集体经济高质量发展三年行动计划。与片区直接相关的条款在“整合农村土地空间行动”：充分利用全域土地综合整治、“五好两宜”和美乡村建设、特色村落风貌保护传承等综合措施，“留改拆”并举将零星插花小块存量集体建设用地整治归并为大宗地块，并将低效建设用地减量化指标按不低于5%比例统筹使用。其余工具包括村村联合抱团发展、“乡村CEO”培养计划、融资担保与贴息贴费、经营管理人员考核评价机制等。",
        slug="chongming-jitijingji-sannianxingdongjihua", areas=[], events=[]),
    "08": dict(
        title="关于印发《松江区推进乡村全面振兴示范区“十五五”规划》的通知",
        doc_no="沪松府〔2026〕76号",
        issuer="上海市松江区人民政府",
        county_code="310117", issued_ymd="2026-07-08", published_ymd="2026-08-03",
        doc_type="规划", instruments="财政,土地,组织,考核,规划,人才,金融,产业,数字",
        scope_desc="松江区全域，构建“一区两翼多组团”；浦南绿色发展实践区涵盖叶榭、泖港、新浜、石湖荡四镇，连片建设和美乡村",
        summary="松江区乡村全面振兴“十五五”规划。空间格局上以浦南绿色发展实践区为主阵地，涵盖叶榭、泖港、新浜、石湖荡四镇，要求连片建设和美乡村、深化一三产融合；另提出推进新浜现代设施农业片区建设、布局花文旅融合片区。指标含宜居宜业和美乡村覆盖率（54%→60%）。要素端明确调整财税分成与土地出让金返还比例、用好点状供地、推进全域土地综合整治、构建财政金融保险社会资本多元投入机制。",
        slug="songjiang-shiwuwu-guihua",
        areas=[{"area_id": "A310002", "entity_type": "area", "rel": "mention"},
               {"area_id": "A310004", "entity_type": "area", "rel": "mention"}],
        events=[]),
    "09": dict(
        title="闵行区人民政府关于印发《“大浦江”区域“十五五”规划》的通知",
        doc_no="闵府发〔2026〕30号",
        issuer="上海市闵行区人民政府",
        county_code="310112", issued_ymd="2026-07-30", published_ymd="2026-08-07",
        doc_type="规划", instruments="土地,考核,规划,人才,产业,数字",
        scope_desc="“大浦江”区域（浦江镇、浦锦街道）；附件名词解释明确浦江镇“五好两宜”试点区域为正义村、汇南村等10个村",
        summary="闵行区“大浦江”区域（浦江镇、浦锦街道）“十五五”规划。乡村振兴部分设“推进乡村振兴连片发展”任务，要求全面完成“沪派江南”正义单元及市级土地综合整治项目建设、“五好两宜”和美乡村项目建设，统筹编制非保留村近中远期实施计划；附件名词解释明确浦江镇“五好两宜”试点区域为正义村、汇南村、汇中村、汇东村、汇红村、汇北村、汇西村、先进村、北徐村、新风村10个村。要素端提出用足用好集体经营性建设用地“点状供地”政策，并将规划实施情况纳入年度绩效考核体系。",
        slug="minhang-dapujiang-shiwuwu-guihua",
        areas=[{"area_id": "A310008", "entity_type": "area", "rel": "support"}],
        events=[]),
}


def load_areas():
    ids = set()
    for ln in COUNTIES.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if not ln.strip():
            continue
        for a in ln.split(",")[5].split("|"):
            ids.add(a.strip())
    return ids


def main():
    recs = []
    if OUT.exists():
        for ln in OUT.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                recs.append(json.loads(ln))
    for p in sorted(PARTS.glob("[0-9][0-9]-*.json")):
        recs.append(json.loads(p.read_text(encoding="utf-8").strip()))
    for key, m in META.items():
        body = (TEXT / f"{key}.md").read_text(encoding="utf-8").strip()
        recs.append({
            "title": m["title"], "doc_no": m["doc_no"], "issuer": m["issuer"],
            "issuer_level": "county", "issued_ymd": m["issued_ymd"],
            "published_ymd": m["published_ymd"], "doc_type": m["doc_type"],
            "source_kind": "政策文件", "province_code": "310000",
            "city_code": "310000", "county_code": m["county_code"],
            "instruments": m["instruments"], "scope_desc": m["scope_desc"],
            "target_areas": "", "budget_wan": "", "valid_state": "现行有效",
            "url": URLS[key], "credibility": "A", "summary": m["summary"],
            "slug": m["slug"], "fetched_at": "2026-11-05",
            "full_text": body, "areas": m["areas"], "events": m["events"],
        })

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        seen = set()
        dedup = []
        for r in recs:
            k = r["slug"]
            if k in seen:
                continue
            seen.add(k)
            dedup.append(r)
        recs = dedup
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    allowed = load_areas()
    enum = {"财政", "土地", "组织", "考核", "规划", "人才", "金融", "产业", "数字"}
    print(f"records={len(recs)}")
    bad = 0
    for i, r in enumerate(recs, 1):
        han = len(re.findall(r"[\u4e00-\u9fff]", r["full_text"]))
        probs = []
        if not r["url"].split("/")[2].endswith(".gov.cn"):
            probs.append("URL_NOT_GOV")
        if han < 300:
            probs.append(f"SHORT({han})")
        for a in r["areas"]:
            if a["area_id"] not in allowed:
                probs.append("AREA_NOT_IN_LIST:" + a["area_id"])
        for v in filter(None, r["instruments"].split(",")):
            if v not in enum:
                probs.append("BAD_INSTR:" + v)
        if "policy_id" in r:
            probs.append("HAS_ID")
        if probs:
            bad += 1
        print(f"  {i:02d} han={han:6d} areas={len(r['areas'])} {r['doc_no'] or '(无文号)':<22} "
              f"{r['title'][:30]} {'; '.join(probs)}")
    print("issues=", bad)


main()
