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

ocr = io.open(r"C:\Users\zjh22\AppData\Local\Temp\wc_plan.md", encoding="utf-8").read().strip()
head = (
    "> 原件为纯图片 PDF（无文本层），以下为 OCR 转录，行序按识别顺序保留，未改动文字。\n"
    "> 已知识别偏差：大峃镇→「大出镇」、垟地边→「样地边/地边村」、铜铃山→「钢铃山」、"
    "畲族→「鑫族」、百丈漈→「百丈源」。原件 URL 见记录 url 字段。\n\n"
)
full_text = head + ocr

rec = {
    "title": "文成县“县城—中心镇—重点村”发展轴空间专项规划（2025—2035年）公示稿图板",
    "doc_no": "",
    "issuer": "文成县自然资源和规划局",
    "issuer_level": "county",
    "issued_ymd": "",
    "published_ymd": "2025-05-29",
    "doc_type": "规划",
    "source_kind": "政策文件",
    "province_code": "330000",
    "city_code": "330300",
    "county_code": "330328",
    "instruments": "规划,发展轴,重点村片区组团,片区组团,农文旅,产业,强城兴村融合",
    "scope_desc": "文成县域发展轴：县城1个大峃镇，重点镇2个（黄坦镇、百丈漈镇），"
    "重点村7个（石庄村、武阳村、让川民族村、共宅村、坦歧村、铜铃村、垟地边村），辐射带动村38个；"
    "逐一列出石庄、武阳、让川、共宅、垟地边、铜铃、坦歧7个重点村片区组团的定位与空间布局",
    "target_areas": 7,
    "budget_wan": "",
    "valid_state": "草案公示稿",
    "credibility": "A",
    "summary": "文成县自然资源和规划局公示的发展轴空间专项规划公示稿图板（3 页，纯图片 PDF，经 OCR 转录）。"
    "规划把县域发展轴落到“县城1个+重点镇2个+重点村7个+辐射带动村38个”，"
    "并逐片给出重点村片区组团的名称与空间布局：百丈镇石庄村“一核两带三区”、"
    "南田镇武阳村“两廊三区块”、西坑畲族镇让川民族村“三带”、黄坦镇共宅村“一核两圈三带”、"
    "巨屿镇垟地边村“一江两岸水经济悦动圈”，另有铜铃山镇铜铃村、坦歧村两个片区组团。"
    "这七片是本库文成石庄、武阳、让川、共宅、垟地边五个片区的命名依据。",
    "slug": "zj-wz-wc-fazhanzhou-guihua-gongshi-tuban",
    "areas": [
        {"area_id": "A330170", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330171", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330172", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330173", "entity_type": "area", "rel": "primary"},
        {"area_id": "A330283", "entity_type": "area", "rel": "primary"},
    ],
    "events": [
        {"area_id": "A330170", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-05-29", "note": "规划公示稿列为百丈镇石庄村重点村片区组团"},
        {"area_id": "A330171", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-05-29", "note": "规划公示稿列为南田镇武阳村重点村片区组团"},
        {"area_id": "A330172", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-05-29", "note": "规划公示稿列为西坑畲族镇让川民族村重点村片区组团"},
        {"area_id": "A330173", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-05-29", "note": "规划公示稿列为黄坦镇共宅村重点村片区组团"},
        {"area_id": "A330283", "entity_type": "area", "event_type": "规划设立", "ymd": "2025-05-29", "note": "规划公示稿列为巨屿镇垟地边村重点村片区组团（OCR 作「地边村」）"},
    ],
    "url": "https://www.wencheng.gov.cn/api-gateway/jpaas-web-server/front/document/file-download?fileUrl=/cms_files/jcms1/web2647/site/attach/0/c1d978da756a4988a3e1b230b450286e.pdf",
    "fetched_at": "2026-11-10",
    "full_text": full_text,
    "full_text_chars": len(full_text),
}

existing = set()
for line in io.open(BATCH, encoding="utf-8"):
    line = line.strip()
    if line:
        existing.add(json.loads(line)["url"])
assert rec["url"] not in existing, "dup url"
ordered = {k: rec[k] for k in ORDER}
with io.open(BATCH, "a", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(ordered, ensure_ascii=False) + "\n")
print("ok, total lines", sum(1 for _ in io.open(BATCH, encoding="utf-8")))
