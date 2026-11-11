import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")
rec = {
 "title": "院东头镇：锚定「十五五」目标 实干担当促新篇（政务访谈）",
 "doc_no": "", "issuer": "沂水县院东头镇人民政府", "issuer_level": "town",
 "issued_ymd": "", "published_ymd": "", "doc_type": "动态", "source_kind": "部门动态",
 "province_code": "370000", "city_code": "371300", "county_code": "371323",
 "instruments": "规划,产业,治理,片区化推进,富美姜山,片区重点项目",
 "scope_desc": "落实全县片区化推进乡村振兴部署，高标准打造「富美姜山」乡村振兴片区，5个片区重点项目有序推进",
 "target_areas": "", "budget_wan": "", "valid_state": "",
 "url": "https://www.yishui.gov.cn/zxft_content.jsp?urltype=interview.InterviewContentURL&wbtreeid=1001&interview=MjAxMw%3D%3D",
 "credibility": "B",
 "summary": "沂水县院东头镇政务访谈。明确落实全县片区化推进乡村振兴部署，高标准打造「富美姜山」乡村振兴片区，坚持产业沿路集聚、风貌沿线塑造、治理全域提升，5个片区重点项目有序推进。",
 "slug": "sd-ly-ys-yuandongtou-zhengwufangtan",
 "areas": [{"area_id": "A370066", "entity_type": "area", "rel": "support"}],
 "events": []
}
with io.open(os.path.join(HERE, "_sd09_part.jsonl"), "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("part written")
