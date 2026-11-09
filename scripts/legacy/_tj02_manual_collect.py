"""一次性：主控直采 TJ02（静海区）剩余记录 —— 子代理在本分片反复挂死，改由主控手工抓取。

只写 data/stage/batches/POL-TJ02-policy.jsonl，追加，不分配 ID。
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "stage" / "batches" / "POL-TJ02-policy.jsonl"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=45).read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def body_of(html: str) -> str:
    """切出正文：从标题第二次出现处到「相关文档：」之间。"""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>|</td>|</tr>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    joined = "\n".join(lines)
    start = joined.find("主任、各位副主任")
    if start < 0:
        start = 0
    end = joined.find("相关文档：")
    if end < 0:
        end = len(joined)
    return joined[start:end].strip()


RECORDS = [
    {
        "url": "http://www.tjjh.gov.cn/jhqzf/xwzx_28970/ztzl/rdgk/202506/t20250609_6951385.html",
        "title": "天津市静海区人民政府关于静海区2024年乡村振兴促进工作情况的报告",
        "doc_no": "",
        "issuer": "天津市静海区人民政府",
        "issuer_level": "county",
        "issued_ymd": "",
        "published_ymd": "2025-06-09",
        "doc_type": "报告",
        "source_kind": "部门动态",
        "province_code": "120000",
        "city_code": "120000",
        "county_code": "120118",
        "instruments": "产业,乡村旅游,人居环境,积分制,集体经济,土地",
        "scope_desc": "全区18个乡镇；乡村旅游重点片区建设已完成独流镇友好街、台头镇北二堡与中二堡基础设施提升",
        "target_areas": "",
        "budget_wan": "",
        "valid_state": "现行有效",
        "credibility": "B",
        "summary": "静海区政府向区三届人大常委会三十次会议所作的2024年度乡村振兴促进工作情况报告，"
                   "含农业综合生产能力、乡村产业、人居环境、乡村治理、农民增收五方面进展与下一步安排；"
                   "明确开展乡村旅游重点片区建设，已完成独流镇友好街（村）、台头镇北二堡、中二堡村庄基础设施提升项目。",
        "slug": "sd-jinghai-2024-xiangcun-zhenxing-cujin-gongzuo-baogao",
        "fetched_at": "2026-11-08",
        "areas": [{"area_id": "A120007", "entity_type": "area", "rel": "support"}],
        "events": [],
    },
    {
        "url": "http://www.tjjh.gov.cn/jhqzf//xwzx_28970/ztzl/rdgk/202512/t20251229_7209706.html",
        "title": "天津市静海区人民政府关于天津市静海区2025年上半年国民经济和社会发展计划执行情况的报告",
        "doc_no": "",
        "issuer": "天津市静海区人民政府",
        "issuer_level": "county",
        "issued_ymd": "",
        "published_ymd": "2025-12-29",
        "doc_type": "报告",
        "source_kind": "部门动态",
        "province_code": "120000",
        "city_code": "120000",
        "county_code": "120118",
        "instruments": "产业,规划,集体经济,土地",
        "scope_desc": "全区；乡村振兴段含国家现代农业产业园、休闲旅游精品线路、人居环境整治与延包试点",
        "target_areas": "",
        "budget_wan": "",
        "valid_state": "现行有效",
        "credibility": "B",
        "summary": "静海区2025年上半年国民经济和社会发展计划执行情况报告，乡村振兴部分记国家现代农业产业园通过首次绩效评估、"
                   "休闲旅游线路获农业农村部推介、农村人居环境整改点位3200余处、二轮延包试点推进；下半年安排含3个乡村振兴示范村创建。",
        "slug": "sd-jinghai-2025-shangbannian-jihua-zhixing-baogao",
        "fetched_at": "2026-11-08",
        "areas": [],
        "events": [],
    },
]


def main() -> int:
    written = 0
    for rec in RECORDS:
        html = fetch(rec["url"])
        body = body_of(html)
        cn = len(re.findall(r"[\u4e00-\u9fa5]", body))
        if cn < 500:
            print(f"!! 正文过短（{cn} 汉字），跳过：{rec['title']}")
            continue
        rec = dict(rec)
        rec["full_text"] = body
        with OUT.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        written += 1
        print(f"+ {cn} 汉字  {rec['title'][:44]}")
    print(f"追加 {written} 条 -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
