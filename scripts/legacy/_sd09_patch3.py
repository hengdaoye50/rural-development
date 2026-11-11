import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")
P = {"1045/50226": {
  "title": "工农手拉手 城乡一起走——山东临沂费县做强镇域经济推动城乡融合发展观察",
  "issuer": "临沂市农业农村局",
  "issuer_level": "city",
  "doc_type": "动态",
  "source_kind": "新闻发布",
  "instruments": "规划,组织,产业,财政,人才,百千工程,乡村振兴示范片区,四雁工程,党支部领办合作社,工农连芯,产城融合",
  "scope_desc": "探沂镇以「工农连芯」乡村振兴片区为双引擎之一；片区覆盖4个村庄，中心村为王管疃村",
  "budget_wan": "",
  "summary": "临沂市农业农村局网站「部门信息」转载农民日报对费县的调研报道。载明费县以探沂镇为试点，以「工农手拉手、城乡一起走」为目标，以做强镇域经济和建设乡村振兴示范片区为「双引擎」；2022年临沂部署「百千工程」，以镇域为单位建设乡村振兴示范片区，每个片区覆盖10个村左右，「每年抓一片，抓一片成一片」。探沂镇建设的「工农连芯」乡村振兴片区覆盖4个村庄，实现党建融合连片规划、基础设施连片提升、资源要素连片整合、产业联动连片共富，中心村为王管疃村。",
  "areas": [{"area_id": "A370184", "entity_type": "area", "rel": "support"}],
  "events": [{"area_id": "A370184", "entity_type": "area", "event_type": "建设",
              "ymd": "", "note": "探沂镇以百千工程为载体建设「工农连芯」片区，覆盖4个村，中心村王管疃村"}]
}}
recs = [json.loads(l) for l in io.open(TARGET, encoding="utf-8") if l.strip()]
n = 0
for o in recs:
    for k, v in P.items():
        if k in o.get("url", ""):
            o.update(v); n += 1; print("PATCHED:", o["title"][:50])
with io.open(TARGET, "w", encoding="utf-8", newline="\n") as f:
    for o in recs:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print("records:", len(recs), "patched:", n)
