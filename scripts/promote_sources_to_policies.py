# -*- coding: utf-8 -*-
"""把 .gov.cn 的 `source` 升格为 `policy` 并挂接 primary。

背景：早期采集把一批 .gov.cn 原文记进了 `source`（第一手证据），没走政策层；
于是这些片区在口径里永远是「无 primary/support」。本脚本按规则升格，而不是重新采。

规则：
  - 只处理 `source.url` 含 `.gov.cn`、`credibility ∈ {A,B}`、`local_path` 是真实文件、有 `title`
  - 同一 URL 只建一条 policy（多片区共用）
  - 挂接条件：**片区名（或 name_norm）出现在政策全文中** → `rel=primary`；出现在标题里也算
  - issuer_level 由域名/标题推断：`nyncj`/`nyw`/`nync` → city/county（按 URL 里地名与 region 匹配），
    省级域名（`xx.gov.cn` 且 host 是省厅）→ province；无法判定 → unknown（不阻断）
  - 不写 `data/clean`：生成 stage JSONL -> `ingest_policy.py`，再用 `add_area_policy_link.py` 挂接

用法：
  python scripts/promote_sources_to_policies.py --dry-run
  python scripts/promote_sources_to_policies.py
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BATCH = ROOT / "data" / "stage" / "batches" / "POL-promote-sources-policy.jsonl"
PY = sys.executable


def issuer_level(host: str, title: str, policy_level_hint: str) -> str:
    if re.search(r"\.(gov)\.cn$", host) is None:
        pass
    sub = host.split(".")[0]
    # 常见：nyncj=农业农村局、nyw、nync、zfb、fgw；省级厅域名多为 xx.gov.cn 直接在省厅
    if re.search(r"(nyncj|nyw|nync|czj|whhlyj|fzggw)", sub):
        return "county" if policy_level_hint == "county" else "city"
    if re.search(r"(wlgd|nynct|nync|gov)$", sub) and policy_level_hint:
        return policy_level_hint
    return policy_level_hint or "unknown"


def main() -> int:
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    region = {r["region_code"]: dict(r) for r in con.execute("select * from region")}

    # 目标：无 primary/support 的在册片区
    targets = {r["area_id"]: dict(r) for r in con.execute("""
        select a.area_id, a.name, a.name_norm, a.province_code, a.city_code, a.county_code
        from area a where a.record_state='active' and a.status<>'待核'
          and not exists(select 1 from area_policy_map m where m.area_id=a.area_id
                         and m.rel in ('primary','support'))""")}

    cands = list(con.execute("""
        select distinct s.source_id, s.url, s.title, s.publisher, s.published_ymd,
               s.credibility, s.local_path, s.hash_sha256
        from source s join area_source_map m on m.source_id=s.source_id
        where m.area_id in (select value from json_each(?))
          and s.url like '%gov.cn%' and s.credibility in ('A','B')
          and coalesce(s.local_path,'') <> '' and coalesce(s.title,'') <> ''
          and s.url not in (select coalesce(url,'') from policy)""",
        (json.dumps(list(targets)),)))

    recs, links = {}, []
    for s in cands:
        f = ROOT / s["local_path"]
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        url = s["url"].strip()
        rec = recs.setdefault(url, {
            "url": url, "title": s["title"].strip(), "issuer": (s["publisher"] or "").strip(),
            "issuer_level": "unknown", "doc_type": "动态", "source_kind": "政务动态",
            "published_ymd": (s["published_ymd"] or "").strip(),
            "credibility": s["credibility"], "full_text": text,
        })
        # 哪些目标片区在这份文本/标题里出现
        for aid, a in targets.items():
            nm = (a["name"] or "").strip()
            nn = (a["name_norm"] or "").strip()
            if not nm:
                continue
            core = re.sub(r"(乡村振兴)?(示范)?片区(组团)?|样板片区|示范带|示范片|和美乡村", "", nm).strip()
            if nm in text or nm in rec["title"] or (nn and nn in text):
                rec.setdefault("_areas", set()).add((aid, "primary"))
            elif len(core) >= 3 and core in text:
                rec.setdefault("_areas", set()).add((aid, "support"))

    recs = {u: r for u, r in recs.items() if r.get("_areas")}
    for u, r in recs.items():
        host = urlparse(u).netloc
        pairs = list(r.pop("_areas"))
        aids = [a for a, _ in pairs]
        prov = [targets[x]["province_code"] for x in aids]
        city = [targets[x]["city_code"] for x in aids]
        r["issuer_level"] = issuer_level(host, r["title"], "county" if len({targets[x]["county_code"] for x in aids}) == 1 else "city")
        r["province_code"] = max(set(prov), key=prov.count) if prov else ""
        r["city_code"] = max(set(city), key=city.count) if city else ""
        r["_links"] = pairs

    print(f"可升格来源 {len(recs)} 条，覆盖片区 {sum(len(r['_links']) for r in recs.values())} 个")
    for r in list(recs.values())[:6]:
        print("  ", r["title"][:40], "|", r["issuer_level"], "|", len(r["_links"]), "片区")
    if dry:
        print("dry-run，未写盘")
        return 0

    BATCH.parent.mkdir(parents=True, exist_ok=True)
    with BATCH.open("w", encoding="utf-8") as f:
        for r in recs.values():
            row = {k: v for k, v in r.items() if not k.startswith("_")}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("批次 ->", BATCH.relative_to(ROOT), f"{len(recs)} 条")
    res = subprocess.run([PY, str(ROOT / "scripts" / "ingest_policy.py"), str(BATCH)],
                         capture_output=True, text=True, encoding="utf-8")
    print(res.stdout.strip().splitlines()[-3:])

    # 先合并重建，让 policy 进库（add_area_policy_link 按库校验）
    for s in ("merge_by_province.py", "build_db.py"):
        r2 = subprocess.run([PY, str(ROOT / "scripts" / s)],
                            capture_output=True, text=True, encoding="utf-8")
        print(s, r2.stdout.strip().splitlines()[-1:])

    # 建 url/title -> policy_id 映射并挂接
    # 注意：ingest_policy 按「规范化标题+县」去重，同文不同 URL 会被跳过，
    # 所以除了 url 还要按标题映射，否则会把已存在的 policy 当成未入库。
    def title_key(t: str) -> str:
        return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-]+", "", t or "")

    con2 = sqlite3.connect(DB)
    con2.row_factory = sqlite3.Row
    pmap = {r["url"]: r["policy_id"] for r in con2.execute("select policy_id, url from policy")}
    tmap = {}
    for r in con2.execute("select policy_id, title from policy"):
        tmap.setdefault(title_key(r["title"]), r["policy_id"])
    added = 0
    for r in recs.values():
        pid = pmap.get(r["url"]) or tmap.get(title_key(r["title"]))
        if not pid:
            continue
        for aid, rel in r["_links"]:
            res = subprocess.run([PY, str(ROOT / "scripts" / "add_area_policy_link.py"),
                                  aid, pid, rel, "由 .gov.cn source 升格（正文点名/核心词命中）"],
                                 capture_output=True, text=True, encoding="utf-8")
            if res.returncode == 0 and "跳过" not in res.stdout:
                added += 1
    print("挂接新增", added)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
