# -*- coding: utf-8 -*-
"""修正升格批次的 policy 层级字段，并把 primary/support 挂上去。

升格时只填了 province/city，没填 county，触发 validate「issuer_level=county 但 county_code 为空」。
本脚本：按批次 URL 找到这些 policy，若关联片区同属一个县则补 county_code，否则 issuer_level 降为 city；
写回 by_province，再按「片区名命中」挂 primary/support。
"""
from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BP = ROOT / "data" / "clean" / "by_province"
BATCH = ROOT / "data" / "stage" / "batches" / "POL-promote-sources-policy.jsonl"
PY = sys.executable


def read(p):
    with p.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def write(p, hdr, rows):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})
    os.replace(tmp, p)


def title_key(t):
    return re.sub(r"[\s\u3000（）()《》〈〉「」【】\[\]、，,。.：:；;“”\"'·—\-]+", "", t or "")


def main() -> int:
    dry = "--dry-run" in sys.argv
    urls, titles = set(), set()
    if BATCH.exists():
        for line in BATCH.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            urls.add(d.get("url", ""))
            titles.add(title_key(d.get("title", "")))

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    # 每个 policy 关联的片区（通过 source→area 或已挂接）
    pol_areas: dict[str, set[str]] = {}
    for r in con.execute("""select p.policy_id, s.url, s.title, a.area_id, a.county_code
        from policy p join source s on s.url = p.url
        join area_source_map m on m.source_id = s.source_id
        join area a on a.area_id = m.area_id"""):
        pol_areas.setdefault(r["policy_id"], set()).add(r["county_code"])
    target = {r["policy_id"]: r for r in con.execute("select policy_id, title, url, issuer_level from policy")
              if r["url"] in urls or title_key(r["title"]) in titles}

    # 写回 by_province
    fix = 0
    for p in sorted(BP.glob("*-policy.csv")):
        hdr, rows = read(p)
        ch = False
        for r in rows:
            pid = r.get("policy_id")
            if pid not in target:
                continue
            counties = {c for c in pol_areas.get(pid, set()) if c}
            if len(counties) == 1:
                r["county_code"] = counties.pop()
                if (r.get("issuer_level") or "") not in ("province", "city", "county", "town"):
                    r["issuer_level"] = "county"
            else:
                r["issuer_level"] = "city"
            ch = True
            fix += 1
        if ch and not dry:
            write(p, hdr, rows)
    print("修正 policy", fix, "（dry-run" if dry else "（已写回", "）")
    if dry:
        return 0

    for s in ("merge_by_province.py", "build_db.py"):
        subprocess.run([PY, str(ROOT / "scripts" / s)], capture_output=True, text=True, encoding="utf-8")

    # 挂接
    con2 = sqlite3.connect(DB)
    con2.row_factory = sqlite3.Row
    pmap = {r["url"]: r["policy_id"] for r in con2.execute("select policy_id, url from policy")}
    tmap = {}
    for r in con2.execute("select policy_id, title from policy"):
        tmap.setdefault(title_key(r["title"]), r["policy_id"])
    # 片区名
    areas = {r["area_id"]: dict(r) for r in con2.execute(
        "select area_id, name, name_norm, county_code from area where record_state='active'")}
    con3 = sqlite3.connect(DB)
    con3.row_factory = sqlite3.Row
    added = 0
    for line in BATCH.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        pid = pmap.get(d["url"]) or tmap.get(title_key(d["title"]))
        if not pid:
            continue
        text = d.get("full_text", "")
        for aid, a in areas.items():
            nm = (a["name"] or "").strip()
            if not nm:
                continue
            core = re.sub(r"(乡村振兴)?(示范)?片区(组团)?|样板片区|示范带|示范片|和美乡村", "", nm).strip()
            rel = "primary" if (nm in text or nm in d["title"]) else ("support" if len(core) >= 3 and core in text else None)
            if not rel:
                continue
            has = con3.execute("""select count(*) from area_policy_map where area_id=? and policy_id=?""",
                               (aid, pid)).fetchone()[0]
            if has:
                continue
            res = subprocess.run([PY, str(ROOT / "scripts" / "add_area_policy_link.py"),
                                  aid, pid, rel, "由 .gov.cn source 升格（正文命中）"],
                                 capture_output=True, text=True, encoding="utf-8")
            if res.returncode == 0:
                added += 1
    print("挂接新增", added)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
