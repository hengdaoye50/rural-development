"""从现有 source 表筛出政策层候选，输出到 data/stage/policy-candidates.csv。

用途：P1 存量盘活。不写 clean、不建 policy 记录——只产出带优先级的待采清单，
供按 docs/07-政策层.md §6 流程逐条补全文后正式入库。

筛选：仅 .gov.cn 域名；排除黑名单；标题或正文含政策文种/文号者优先。
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "data" / "stage" / "policy-candidates.csv"

DOC_NO = re.compile(r"[\u4e00-\u9fa5]{1,12}[〔\[]\s*(?:19|20)\d{2}\s*[〕\]]\s*\d+\s*号")
DOC_TYPE = re.compile(r"(意见|方案|规划|通知|办法|批复|决定|导则|名单|公告)")
DENY = (
    "sohu.com", "sina.com.cn", "sina.com", "qq.com", "163.com",
    "jiemian.com", "52hrtt.com", "toutiao.com", "baidu.com",
    "weixin.qq.com", "mp.weixin", "zhihu.com", "ifeng.com",
)

PROV = {
    "11": "北京", "12": "天津", "13": "河北", "14": "山西", "15": "内蒙古",
    "21": "辽宁", "22": "吉林", "23": "黑龙江", "31": "上海", "32": "江苏",
    "33": "浙江", "34": "安徽", "35": "福建", "36": "江西", "37": "山东",
    "41": "河南", "42": "湖北", "43": "湖南", "44": "广东", "45": "广西",
    "46": "海南", "50": "重庆", "51": "四川", "52": "贵州", "53": "云南",
    "54": "西藏", "61": "陕西", "62": "甘肃", "63": "青海", "64": "宁夏",
    "65": "新疆",
}

FIELDS = [
    "priority", "source_id", "url", "title", "publisher", "published_ymd",
    "doc_no_guess", "doc_type_guess", "level_hint",
    "province_code", "city_code", "county_code",
    "linked_areas", "linked_area_ids", "reason",
]


def level_hint(publisher: str, host: str) -> str:
    p = publisher or ""
    if any(k in p for k in ("省委", "省政府", "省农业", "省厅", "自治区", "农业农村部", "部")):
        return "province"
    if any(k in p for k in ("市农业", "市人民", "市政府", "市委")):
        return "city"
    if any(k in p for k in ("县", "区人民", "区农业", "镇")):
        return "county"
    return ""


def main() -> int:
    if not DB.exists():
        print(f"DB 不存在: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # source -> 关联片区（含 belt）
    link = defaultdict(list)
    for r in cur.execute(
        """select m.source_id, m.area_id, m.entity_type,
                  coalesce(a.name, b.name) nm,
                  coalesce(a.province_code, b.province_code) pc,
                  coalesce(a.city_code, b.city_code) cc,
                  coalesce(a.county_code, b.county_code) cty
           from area_source_map m
           left join area a on m.entity_type='area' and a.area_id=m.area_id
           left join belt b on m.entity_type='belt' and b.belt_id=m.area_id"""
    ):
        link[r["source_id"]].append(r)

    rows = []
    for r in cur.execute("select * from source"):
        url = (r["url"] or "").lower()
        if ".gov.cn" not in url:
            continue
        if any(b in url for b in DENY):
            continue

        text = f"{r['title'] or ''} {r['excerpt'] or ''}"
        m_doc = DOC_NO.search(text)
        m_type = DOC_TYPE.search(r["title"] or "")
        doc_no = m_doc.group(0) if m_doc else ""
        doc_type = m_type.group(1) if m_type else ""

        # 优先级：有文号 > 标题含文种 > 其他政府动态
        if doc_no:
            pri, reason = 1, "含发文字号"
        elif doc_type:
            pri, reason = 2, f"标题含文种:{doc_type}"
        else:
            pri, reason = 3, "政府网动态/其他"

        links = link.get(r["source_id"], [])
        pcs = {x["pc"] for x in links if x["pc"]}
        ccs = {x["cc"] for x in links if x["cc"]}
        ctys = {x["cty"] for x in links if x["cty"]}
        pcode = sorted(pcs)[0] if pcs else ""
        host = urlparse(r["url"]).netloc

        rows.append({
            "priority": pri,
            "source_id": r["source_id"],
            "url": r["url"],
            "title": r["title"] or "",
            "publisher": r["publisher"] or "",
            "published_ymd": r["published_ymd"] or "",
            "doc_no_guess": doc_no,
            "doc_type_guess": doc_type,
            "level_hint": level_hint(r["publisher"], host),
            "province_code": pcode,
            "city_code": sorted(ccs)[0] if len(ccs) == 1 else "",
            "county_code": sorted(ctys)[0] if len(ctys) == 1 else "",
            "linked_areas": len(links),
            "linked_area_ids": "|".join(sorted({x["area_id"] for x in links[:5]})),
            "reason": reason,
        })

    rows.sort(key=lambda x: (x["priority"], -x["linked_areas"], x["province_code"], x["source_id"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    by_pri = defaultdict(int)
    for r in rows:
        by_pri[r["priority"]] += 1
    print(f"候选 {len(rows)} 条 -> {OUT}")
    print(f"  P1 含发文字号: {by_pri[1]}")
    print(f"  P2 含文种:     {by_pri[2]}")
    print(f"  P3 政府动态:   {by_pri[3]}")
    provs = sorted({r["province_code"] for r in rows if r["province_code"]})
    print(f"  涉及省级码 {len(provs)}: {' '.join(PROV.get(p[:2], p) for p in provs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
