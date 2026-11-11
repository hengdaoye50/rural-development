import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")
PATCH = {
 "1021/209762": {
  "published_ymd": "2026-04-16",
  "instruments": "组织,规划,产业,片区化推进,考察调研",
  "summary": "2026年4月16日济宁市副市长王庆带队到蒙阴县考察调研乡村振兴片区建设。考察团先后到桃墟镇「诗意田园·和美桃墟」片区百花峪村、垛庄镇沂蒙华润希望小镇片区水涟峪村实地调研，了解基础设施建设、人居环境整治、乡村旅游开发、特色产业发展等经验，评价蒙阴片区化推进乡村振兴经验可复制可推广。",
  "events": []
 },
 "9322/164184": {
  "issuer": "蒙阴县人民政府",
  "issuer_level": "county",
  "published_ymd": "2023-12-29",
  "doc_no": "",
  "instruments": "规划,产业,文旅,民宿旅游,激活蒙山,五大片区",
  "scope_desc": "桃墟镇以金水前城、树上村庄、百花峪、百泉峪、花果庄五大片区为建设重点",
  "target_areas": 5,
  "summary": "蒙阴县桃墟镇「我为群众办实事」主题新闻发布会专场（索引号myx/2024-0000076）。桃墟镇确定「一三五一」民宿旅游工作思路：一个中心为「激活蒙山」，以引进高端、带动中端、提升低端为三条路径，以金水前城、树上村庄、百花峪、百泉峪、花果庄五大片区为建设重点，目标打造「江北民宿旅游第一镇」，以民宿发展带动全域旅游、助推乡村产业振兴。",
  "areas": [],
  "events": []
 }
}
recs = [json.loads(l) for l in io.open(TARGET, encoding="utf-8") if l.strip()]
n = 0
for o in recs:
    for k, v in PATCH.items():
        if k in o.get("url", ""):
            o.update(v); n += 1; print("PATCHED:", o["title"][:44])
with io.open(TARGET, "w", encoding="utf-8", newline="\n") as f:
    for o in recs:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print("records:", len(recs), "patched:", n)
