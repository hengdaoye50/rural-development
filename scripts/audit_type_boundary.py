"""`area` 与 `belt` 的类型边界审计（按 docs/01 §10.2 的唯一判据）。

判据只有一条，不看名字：
- 有官方设立/批复/名单/挂牌文件 → 应进 `area`（哪怕叫「示范带」「廊带」）
- 只有公开命名与振兴语义、无设立动作 → 应进 `belt`（哪怕叫「片区」）

两个方向都查：
1. area → belt：T03（示范带类）片区，挂着的政策里没有任何一份是设立类文种
   （名单/批复/通知/决定/公示，或标题含「设立/公布/认定/创建」）→ 可能只是被报道命名
2. belt → area：`belt` 名在某份设立类政策的正文里逐字出现 → 可能有设立文件，本该进 area

本脚本**只排序不判定**，输出待裁定清单供人工逐条过。

    python scripts/audit_type_boundary.py
    python scripts/audit_type_boundary.py --csv reports/qa/type-boundary-audit.csv
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "qa" / "type-boundary-audit.csv"

# 设立类文种／标题词：出现即认为该文件具备「设立/命名」效力
SETUP_DOC_TYPES = {"名单", "批复", "通知", "决定", "公示", "意见", "办法"}
SETUP_TITLE_WORDS = ("名单", "批复", "公布", "设立", "认定", "创建", "同意", "示范带", "示范区")


def _is_setup(doc_type: str, title: str) -> bool:
    if (doc_type or "").strip() in SETUP_DOC_TYPES:
        return True
    return any(w in (title or "") for w in SETUP_TITLE_WORDS)


def main(argv: list[str]) -> int:
    if not DB.exists():
        print(f"找不到 {DB}")
        return 1
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    pol = {r["policy_id"]: r for r in con.execute(
        "select policy_id, title, doc_type, doc_no, local_path, province_code from policy")}
    links = {}
    for r in con.execute("select area_id, policy_id, rel from area_policy_map"):
        links.setdefault(r["area_id"], []).append(r["policy_id"])

    out: list[dict[str, str]] = []

    # ---- 方向一：area(T03) -> belt ----
    for r in con.execute("""select a.area_id, a.name, a.province_code, a.type_code,
                                   a.founded_precision, a.founded_ymd
                            from area a
                            where a.record_state='active' and a.status<>'待核'
                              and a.type_code='T03'"""):
        pids = links.get(r["area_id"], [])
        setup = [p for p in pids if p in pol and _is_setup(pol[p]["doc_type"], pol[p]["title"])]
        if setup:
            continue
        out.append({
            "direction": "area->belt",
            "entity_id": r["area_id"],
            "name": r["name"],
            "province_code": r["province_code"],
            "type_code": r["type_code"],
            "linked_policies": len(pids),
            "evidence": "; ".join((pol[p]["title"] or "")[:40] for p in pids[:2]),
            "reason": "T03 但无任何设立类文件（名单/批复/通知/公示）",
        })

    # ---- 方向二：belt -> area（逐字命中设立类政策正文）----
    texts: dict[str, str] = {}
    for pid, p in pol.items():
        lp = p["local_path"]
        if not lp:
            continue
        f = ROOT / lp
        if f.exists():
            texts[pid] = f.read_text(encoding="utf-8", errors="ignore")
    setup_ids = [pid for pid, p in pol.items()
                 if _is_setup(p["doc_type"], p["title"]) and pid in texts]
    print(f"设立类政策 {len(setup_ids)} 份参与正文匹配")

    for r in con.execute("select belt_id, name, province_code from belt where record_state='active'"):
        name = (r["name"] or "").strip()
        core = re.sub(r"(示范带|示范廊带|廊带|示范圈|示范走廊|走廊|片区群|片区|示范片|产业带|精品带)$", "", name)
        key = core if len(core) >= 3 else name
        hit = ""
        for pid in setup_ids:
            # 必须同省：跨省文件里的同名泛称是假阳性来源（山西「城乡融合示范廊带」曾被匹配到天津市委文件）
            if (pol[pid]["province_code"] or "") != (r["province_code"] or ""):
                continue
            if key and key in texts[pid]:
                hit = pid
                break
        if hit:
            out.append({
                "direction": "belt->area",
                "entity_id": r["belt_id"],
                "name": name,
                "province_code": r["province_code"],
                "type_code": "",
                "linked_policies": 0,
                "evidence": f"{hit} {(pol[hit]['title'] or '')[:44]}",
                "reason": "belt 名在设立类政策正文中逐字出现",
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["direction"])
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    c = Counter(r["direction"] for r in out)
    print(f"{len(out)} 条待裁定 -> {OUT.relative_to(ROOT)}")
    print("  " + "，".join(f"{k} {v}" for k, v in c.items()))
    for r in out[:12]:
        print(f"  [{r['direction']}] {r['entity_id']} {r['name'][:30]} | {r['reason'][:30]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
