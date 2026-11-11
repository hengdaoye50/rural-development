import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

BATCH = "data/stage/batches/POL-ZJ03-policy.jsonl"
ORDER = [
    "title", "doc_no", "issuer", "issuer_level", "issued_ymd", "published_ymd",
    "doc_type", "source_kind", "province_code", "city_code", "county_code",
    "instruments", "scope_desc", "target_areas", "budget_wan", "valid_state",
    "credibility", "summary", "slug", "areas", "events", "url", "fetched_at",
    "full_text", "full_text_chars",
]

full_text = io.open(r"C:\Users\zjh22\AppData\Local\Temp\py_plan.txt", encoding="utf-8").read().strip()

rec = {
    "title": "平阳县“县城—中心镇—重点村”发展轴空间专项规划（2025—2035年）公示稿",
    "doc_no": "",
    "issuer": "平阳县自然资源和规划局",
    "issuer_level": "county",
    "issued_ymd": "",
    "published_ymd": "2025-04-15",
    "doc_type": "规划",
    "source_kind": "政策文件",
    "province_code": "330000",
    "city_code": "330300",
    "county_code": "330326",
    "instruments": "规划,发展轴,重点村片区组团,片区组团,农文旅,产业,强城兴村融合,一轴两廊三镇多点",
    "scope_desc": "发展轴涉及昆阳、鳌江、水头、万全、萧江、麻步、腾蛟、凤卧、海西9个乡镇，总面积518.6平方公里、占县域49.3%；轴上常住人口约77.8万人；列16个重点村片区组团及各自产业主题",
    "target_areas": 16,
    "budget_wan": "",
    "valid_state": "草案公示稿",
    "credibility": "A",
    "summary": "平阳县自然资源和规划局公示的发展轴空间专项规划公示稿（图板全文），"
    "总体结构为“一轴两廊、三镇多点”：以县城昆阳为核心打造“V”型发展轴，"
    "东翼沿海科创智造发展廊、中西翼沿江城乡融合发展廊，鳌江、水头、万全三镇协同带动16个中心村组团。"
    "规划逐一列出16个重点村片区组团的镇街、村名与产业主题，"
    "其中万全镇周垟“田园水乡”、鳌江镇岭根“曦揽梅乡”、水头镇新联“黄汤茶乡”、"
    "凤卧镇凤林“绿野红都”、海西镇海湾“慢湾听海”，是库内周垟、岭根、新联、凤林、海湾五个片区的命名依据。"
    "规划同时给出轴上经济体量718.6亿元、占县域92.4%等口径。",
    "slug": "zj-wz-py-fazhanzhou-guihua-gongshigao",
    "areas": [
        {"area_id": "A330175", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330176", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330177", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330178", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330284", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330015", "entity_type": "area", "rel": "mention"},
    ],
    "events": [
        {"area_id": "A330175", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-04-15", "note": "规划公示稿列为万全镇周垟“田园水乡”重点村片区组团"},
        {"area_id": "A330176", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-04-15", "note": "规划公示稿列为鳌江镇岭根“曦揽梅乡”重点村片区组团"},
        {"area_id": "A330177", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-04-15", "note": "规划公示稿列为凤卧镇凤林“绿野红都”重点村片区组团"},
        {"area_id": "A330178", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-04-15", "note": "规划公示稿列为水头镇新联“黄汤茶乡”重点村片区组团"},
        {"area_id": "A330284", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-04-15", "note": "规划公示稿列为海西镇海湾“慢湾听海”重点村片区组团"},
    ],
    "url": "https://www.zjpy.gov.cn/api-gateway/jpaas-web-server/front/document/file-download?fileUrl=/cms_files/jcms1/web1830/site/attach/0/2fe604c2cfad47f19ad735314743c8a2.pdf",
    "fetched_at": "2026-11-10",
    "full_text": full_text,
    "full_text_chars": len(full_text),
}

existing = set()
for line in io.open(BATCH, encoding="utf-8"):
    line = line.strip()
    if line:
        existing.add(json.loads(line)["url"])
assert rec["url"] not in existing
ordered = {k: rec[k] for k in ORDER}
with io.open(BATCH, "a", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(ordered, ensure_ascii=False) + "\n")
print("ok, total lines", sum(1 for _ in io.open(BATCH, encoding="utf-8")))
