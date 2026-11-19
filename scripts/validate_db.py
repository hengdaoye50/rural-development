"""校验 clean CSV / SQLite：必填、枚举、引用完整性、重复名、来源完备。"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT_DIR = ROOT / "reports" / "qa"

TYPE_CODES = {"T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"}
STATUS = {"运行中", "待核", "已撤销", "已更名", "已完成"}
RECORD_STATE = {"active", "superseded", "withdrawn"}
PRECISION = {"day", "month", "year", "unknown"}
CRED = {"A", "B", "C", "D", "E"}
BELT_TYPES = {"带", "圈", "廊", "片", "走廊", "环", "线", "其他"}
BELT_ROLE = {"county", "town", "village", "spine", "node"}

# ---- 政策层（docs/02 数据字典 §4–§5.1、docs/07 政策层） ----
POLICY_LEVEL = {"province", "city", "county", "town", "other"}
DOC_TYPES = {"意见", "方案", "规划", "通知", "办法", "批复", "决定", "导则",
             "名单", "公告", "动态", "答复", "指南", "总结", "报告", "其他"}
# doc_type 为开放词表，清单外取值只提示
DOC_TYPES_HINT = DOC_TYPES | {"新闻发布", "复函", "简报", "纪要", "公报"}
SOURCE_KINDS = {"政策文件", "政府公报", "部门动态", "新闻发布"}
VALID_STATE = {"现行有效", "已废止", "已修订", "试点", "征求意见", "公示中", "未知"}
# valid_state 为开放词表，此处仅为常见值
VALID_STATE_HINT = VALID_STATE | {"有效", "已失效", "失效", "已撤销", "草案"}
POLICY_CRED = {"A", "B"}
# 常用标签，仅为提示用；instruments 是开放词表，允许地方特有提法
INSTRUMENTS_HINT = {"财政", "土地", "组织", "考核", "规划", "人才", "金融", "产业", "数字"}
ENTITY_TYPES = {"area", "belt"}
REL = {"primary", "support", "mention"}
# event_type 为开放词表，此处只是常见值，用于提示而非拦截
EVENT_TYPES_HINT = {
    "设立", "挂牌", "批复", "入选", "扩围", "更名", "撤销",
    "验收", "评估", "资金", "表扬", "观摩", "其他",
    "规划编制", "立项", "推进会", "会议", "项目评审", "项目建设",
    "人大监督", "入选名单", "入选案例", "入选试点", "现场会考察",
}

# 权威门槛：policy 不得来自商业门户/聚合站（docs/07 §3.2）
POLICY_DENY_DOMAINS = (
    "sohu.com", "sina.com.cn", "sina.com", "qq.com", "163.com",
    "jiemian.com", "52hrtt.com", "toutiao.com", "baidu.com",
    "weixin.qq.com", "mp.weixin", "zhihu.com", "ifeng.com",
)

POLICY_REQUIRED = [
    "policy_id", "title", "issuer", "issuer_level", "date_precision",
    "doc_type", "source_kind", "province_code", "valid_state", "url",
    "local_path", "credibility", "fetched_at", "record_state",
    "created_at", "updated_at", "created_by",
]


def _check_policy(policies, area_ids, belt_ids, region_ids):
    issues: list[str] = []
    warnings: list[str] = []
    for p in policies:
        pid = p.get("policy_id") or "<empty>"
        for k in POLICY_REQUIRED:
            if not p.get(k):
                issues.append(f"[policy:{pid}] 缺必填字段 {k}")

        if p.get("issuer_level") and p["issuer_level"] not in POLICY_LEVEL:
            issues.append(f"[policy:{pid}] 非法 issuer_level={p['issuer_level']}")
        if p.get("doc_type") and p["doc_type"] not in DOC_TYPES_HINT:
            warnings.append(f"[policy:{pid}] 非预设文种（开放词表，允许）: {p['doc_type']}")
        if p.get("source_kind") and p["source_kind"] not in SOURCE_KINDS:
            issues.append(f"[policy:{pid}] 非法 source_kind={p['source_kind']}")
        if p.get("valid_state") and p["valid_state"] not in VALID_STATE_HINT:
            warnings.append(f"[policy:{pid}] 非预设时效状态（开放词表，允许）: {p['valid_state']}")
        if p.get("credibility") and p["credibility"] not in POLICY_CRED:
            issues.append(f"[policy:{pid}] credibility 只允许 A/B，实为 {p['credibility']}")
        if p.get("date_precision") and p["date_precision"] not in PRECISION:
            issues.append(f"[policy:{pid}] 非法 date_precision={p['date_precision']}")
        if p.get("record_state") and p["record_state"] not in RECORD_STATE:
            issues.append(f"[policy:{pid}] 非法 record_state={p['record_state']}")

        url = (p.get("url") or "").lower()
        if url and ".gov.cn" not in url:
            issues.append(f"[policy:{pid}] 非 .gov.cn 域名，不得入政策层: {url[:60]}")
        for bad in POLICY_DENY_DOMAINS:
            if bad in url:
                issues.append(f"[policy:{pid}] 命中来源黑名单 {bad}")
                break

        # instruments 是开放词表：预设九类之外的标签（如地方特有提法）照收，不拦截
        inst = p.get("instruments") or ""
        foreign = [
            t.strip() for t in inst.split(",")
            if t.strip() and t.strip() not in INSTRUMENTS_HINT
        ]
        if foreign:
            warnings.append(
                f"[policy:{pid}] 非预设标签（开放词表，允许）: {','.join(foreign)}"
            )

        if p.get("issuer_level") == "county" and not p.get("county_code"):
            issues.append(f"[policy:{pid}] issuer_level=county 但 county_code 为空")
        for code_field in ("province_code", "city_code", "county_code"):
            code = p.get(code_field) or ""
            if code and region_ids and code not in region_ids:
                warnings.append(f"[policy:{pid}] {code_field}={code} 不在 region 表")

        chars = (p.get("full_text_chars") or "").strip()
        if chars:
            try:
                n = int(float(chars))
            except ValueError:
                issues.append(f"[policy:{pid}] full_text_chars 非数值: {chars}")
            else:
                if n < 150 and p.get("doc_type") != "动态":
                    warnings.append(
                        f"[policy:{pid}] 全文仅 {n} 字（doc_type={p.get('doc_type')}），疑似只存了摘录"
                    )

    # doc_no+issuer 唯一（无文号则 url 唯一）
    seen_doc: dict[tuple, str] = {}
    seen_url: dict[str, str] = {}
    for p in policies:
        if p.get("record_state") != "active":
            continue
        pid = p.get("policy_id")
        docno = (p.get("doc_no") or "").strip()
        if docno:
            key = (docno, p.get("issuer") or "")
            if key in seen_doc:
                issues.append(f"[policy] 重复 doc_no+issuer: {key} ({seen_doc[key]} / {pid})")
            else:
                seen_doc[key] = pid
        else:
            u = (p.get("url") or "").strip()
            if u:
                if u in seen_url:
                    issues.append(f"[policy] 无文号但 url 重复: {u[:60]} ({seen_url[u]} / {pid})")
                else:
                    seen_url[u] = pid

    return issues, warnings


def _check_policy_map(rows, policy_ids, area_ids, belt_ids):
    issues: list[str] = []
    for r in rows:
        key = f"{r.get('area_id')}/{r.get('policy_id')}"
        et = r.get("entity_type") or ""
        if et not in ENTITY_TYPES:
            issues.append(f"[area_policy_map:{key}] 非法 entity_type={et}")
        if et == "area" and r.get("area_id") not in area_ids:
            issues.append(f"[area_policy_map:{key}] area_id 不存在")
        if et == "belt" and r.get("area_id") not in belt_ids:
            issues.append(f"[area_policy_map:{key}] belt_id 不存在")
        if r.get("policy_id") not in policy_ids:
            issues.append(f"[area_policy_map:{key}] policy_id 不存在")
        if r.get("rel") and r["rel"] not in REL:
            issues.append(f"[area_policy_map:{key}] 非法 rel={r['rel']}")
    return issues


def _check_event(rows, policy_ids, source_ids, area_ids, belt_ids):
    issues: list[str] = []
    warnings: list[str] = []
    for r in rows:
        eid = r.get("event_id") or "<empty>"
        if not r.get("area_id"):
            issues.append(f"[event:{eid}] 缺 area_id")
        ent = r.get("entity_type") or "area"
        if ent not in ENTITY_TYPES:
            issues.append(f"[event:{eid}] 非法 entity_type={ent}")
        elif ent == "area" and r.get("area_id") not in area_ids:
            issues.append(f"[event:{eid}] area_id 不存在: {r.get('area_id')}")
        elif ent == "belt" and r.get("area_id") not in belt_ids:
            issues.append(f"[event:{eid}] belt_id 不存在: {r.get('area_id')}")
        et = r.get("event_type") or ""
        if not et:
            issues.append(f"[event:{eid}] 缺 event_type")
        elif et not in EVENT_TYPES_HINT:
            warnings.append(f"[event:{eid}] 非预设事件类型（开放词表，允许）: {et}")
        if r.get("source_id") and r["source_id"] not in source_ids:
            issues.append(f"[event:{eid}] source_id 不存在: {r['source_id']}")
        if r.get("policy_id") and r["policy_id"] not in policy_ids:
            issues.append(f"[event:{eid}] policy_id 不存在: {r['policy_id']}")
    return issues, warnings

BELT_REQUIRED = [
    "belt_id", "name", "name_norm", "belt_type", "province_code", "city_code",
    "cover_desc", "year_precision", "record_state",
    "created_at", "updated_at", "created_by",
]

AREA_REQUIRED = [
    "area_id", "name", "name_norm", "type_code", "province_code", "city_code",
    "county_code", "cover_desc", "founded_precision", "status", "record_state",
    "created_at", "updated_at", "created_by",
]


def _rows(name: str) -> list[dict[str, str]]:
    p = CLEAN / name
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate() -> int:
    issues: list[str] = []
    warnings: list[str] = []
    areas = _rows("area.csv")
    sources = _rows("source.csv")
    regions = _rows("region.csv")
    belts = _rows("belt.csv")
    policies = _rows("policy.csv")
    area_policy_map = _rows("area_policy_map.csv")
    area_region_map = _rows("area_region_map.csv")
    events = _rows("event.csv")

    area_ids = {a["area_id"] for a in areas}
    belt_ids = {b["belt_id"] for b in belts}
    region_ids = {r["region_code"] for r in regions}

    for a in areas:
        aid = a.get("area_id") or "<empty>"
        for k in AREA_REQUIRED:
            if not a.get(k):
                issues.append(f"[area:{aid}] 缺必填字段 {k}")
        if a.get("type_code") not in TYPE_CODES:
            issues.append(f"[area:{aid}] 非法 type_code={a.get('type_code')}")
        if a.get("status") not in STATUS:
            issues.append(f"[area:{aid}] 非法 status={a.get('status')}")
        if a.get("record_state") not in RECORD_STATE:
            issues.append(f"[area:{aid}] 非法 record_state={a.get('record_state')}")
        if a.get("founded_precision") not in PRECISION:
            issues.append(f"[area:{aid}] 非法 founded_precision={a.get('founded_precision')}")

    # duplicate active name_norm in same county
    keys = [
        (a["county_code"], a["name_norm"])
        for a in areas
        if a.get("record_state") == "active"
    ]
    for key, n in Counter(keys).items():
        if n > 1:
            issues.append(f"[area] active 重复 name_norm+county: {key} x{n}")

    for s in sources:
        sid = s.get("source_id") or "<empty>"
        for k in ("source_id", "area_id", "url", "title", "publisher", "excerpt", "fetched_at", "credibility"):
            if not s.get(k):
                issues.append(f"[source:{sid}] 缺必填字段 {k}")
        if s.get("credibility") not in CRED:
            issues.append(f"[source:{sid}] 非法 credibility={s.get('credibility')}")
        ref = s.get("area_id") or ""
        if ref and ref not in area_ids and ref not in belt_ids:
            issues.append(f"[source:{sid}] area_id 既非 area 也非 belt: {ref}")
        if s.get("credibility") in {"A", "B", "C"} and not s.get("local_path"):
            warnings.append(f"[source:{sid}] A/B/C 级缺 local_path 快照")
        if s.get("excerpt") and len(s["excerpt"]) < 40:
            issues.append(f"[source:{sid}] excerpt 过短 (<40字)")

    source_by_id = {s.get("source_id"): s for s in sources}
    source_primary = {s.get("area_id") for s in sources}
    region_by_code = {r.get("region_code"): r for r in regions}

    for a in areas:
        aid = a["area_id"]
        sid = a.get("first_source_id") or ""
        linked = (aid in source_primary) or (sid in source_by_id)
        # 引用悬空是硬缺陷：待核可以「证据不足」，但不能「证据不存在」
        if sid and sid not in source_by_id:
            issues.append(f"[area:{aid}] first_source_id={sid} 在 source 表不存在（引用悬空）")
        elif not linked:
            if a.get("status") != "待核":
                issues.append(f"[area:{aid}] 无任何 source（且 status≠待核）")

    # 区划归属：占位码与悬空城市码会让按市/县聚合静默出错
    # 省直辖县级行政区（济源 419001、神农架 429021 等）city_code 等于 county_code，属合法
    placeholder = {r.get("region_code") for r in regions if r.get("name") == r.get("region_code")}
    for a in areas:
        aid = a["area_id"]
        cc = a.get("county_code") or ""
        city = a.get("city_code") or ""
        if cc in placeholder:
            warnings.append(f"[area:{aid}] county_code={cc} 是 region 占位行（name 等于代码），需回原始来源核定")
        if city and city not in region_by_code and city != cc:
            warnings.append(f"[area:{aid}] city_code={city} 在 region 表不存在")

    # 区划归属行完整性：active 片区必须有 area_region_map 行。
    # 缺行不会报错，只会让「按 map 聚合」的县覆盖/分市统计**静默少算**——
    # 2026-11 浙江 13 条就是这样漏的（见 scripts/repair_area_region_map.py）。
    areg_ids = {r.get("area_id") for r in area_region_map}
    for a in areas:
        if a.get("record_state") == "active" and a["area_id"] not in areg_ids:
            issues.append(f"[area:{a['area_id']}] active 但无 area_region_map 行（按 map 聚合会漏算）")
    for r in area_region_map:
        aid = r.get("area_id") or ""
        if aid and aid not in area_ids:
            issues.append(f"[area_region_map:{aid}] area_id 不存在")
        rc = r.get("region_code") or ""
        if rc and rc not in region_ids:
            warnings.append(f"[area_region_map:{aid}] region_code={rc} 不在 region 表")

    # 数值字段必须是整数：国道/省道编号、户数常被灌进来
    for a in areas:
        for f in ("scale_villages", "scale_towns"):
            v = (a.get(f) or "").strip()
            if v and not v.isdigit():
                warnings.append(f"[area:{a['area_id']}] {f}={v!r} 非整数，需复核")

    if regions:
        for r in regions:
            if not r.get("region_code") or not r.get("name") or not r.get("level"):
                issues.append(f"[region] 缺字段: {r}")
    else:
        issues.append("[region] region.csv 为空（试点期至少应有省级）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_ids = {s.get("source_id") for s in sources}

    policy_ids = {p.get("policy_id") for p in policies}
    p_issues, p_warnings = _check_policy(policies, area_ids, belt_ids, region_ids)
    issues.extend(p_issues)
    warnings.extend(p_warnings)
    issues.extend(_check_policy_map(area_policy_map, policy_ids, area_ids, belt_ids))
    e_issues, e_warnings = _check_event(events, policy_ids, source_ids, area_ids, belt_ids)
    issues.extend(e_issues)
    warnings.extend(e_warnings)

    # 省级名单台账：引用与数值必须自洽（docs/02 province_roster）
    rosters = _rows("province_roster.csv")
    prov_ids = {r.get("region_code") for r in regions if r.get("level") == "province"}
    for r in rosters:
        code = r.get("province_code") or "<empty>"
        if code not in prov_ids:
            issues.append(f"[province_roster:{code}] province_code 不是 region 里的省级行")
        pid = (r.get("policy_id") or "").strip()
        if pid and pid not in policy_ids:
            issues.append(f"[province_roster:{code}] policy_id={pid} 不存在")
        sid = (r.get("source_id") or "").strip()
        if sid and sid not in source_ids:
            issues.append(f"[province_roster:{code}] source_id={sid} 不存在")
        for f in ("official_count", "in_db_count"):
            v = (r.get(f) or "").strip()
            if v and not v.isdigit():
                issues.append(f"[province_roster:{code}] {f}={v!r} 非整数")
        if r.get("status") not in {"matched", "partial", "count_only", "not_area", "none"}:
            issues.append(f"[province_roster:{code}] 非法 status={r.get('status')}")
    if not rosters:
        warnings.append("[province_roster] 台账为空（省级层口径未登记）")

    for b in belts:
        bid = b.get("belt_id") or "<empty>"
        for k in BELT_REQUIRED:
            if not b.get(k):
                issues.append(f"[belt:{bid}] 缺必填字段 {k}")
        if b.get("belt_type") not in BELT_TYPES:
            issues.append(f"[belt:{bid}] 非法 belt_type={b.get('belt_type')}")
        if b.get("record_state") not in RECORD_STATE:
            issues.append(f"[belt:{bid}] 非法 record_state={b.get('record_state')}")
        if b.get("year_precision") not in PRECISION:
            issues.append(f"[belt:{bid}] 非法 year_precision={b.get('year_precision')}")
        if b.get("source_id") and b["source_id"] not in source_ids:
            issues.append(f"[belt:{bid}] source_id 不存在: {b['source_id']}")

    bkeys = [
        (b["province_code"], b["name_norm"], b["belt_type"])
        for b in belts
        if b.get("record_state") == "active"
    ]
    for key, n in Counter(bkeys).items():
        if n > 1:
            issues.append(f"[belt] active 重复 key: {key} x{n}")

    out = OUT_DIR / "validate-latest.md"
    lines = [
        "# QA 报告",
        "",
        f"- area: {len(areas)}",
        f"- source: {len(sources)}",
        f"- region: {len(regions)}",
        f"- belt: {len(belts)}",
        f"- policy: {len(policies)}",
        f"- area_policy_map: {len(area_policy_map)}",
        f"- event: {len(events)}",
        f"- issues: {len(issues)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if issues:
        lines.append("## 问题清单")
        lines.extend(f"- {i}" for i in issues)
    else:
        lines.append("问题清单为空。")
    if warnings:
        lines.append("")
        lines.append("## 警告（不阻断）")
        lines.extend(f"- {w}" for w in warnings)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"issues={len(issues)} warnings={len(warnings)} -> {out}")
    for i in issues[:20]:
        print(" -", i)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(validate())
