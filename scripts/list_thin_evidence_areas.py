"""列出「没有 primary/support 依据」的在册片区，作为下一轮补采作业清单。

「有政策依据」的口径见 `docs/02` `rel` 语义与 `reports/qa/policy-link-veracity.md`：
只有 `primary`（设立/批复/命名）与 `support`（点名支持）算依据，`mention` 只算提及。

输出 `reports/qa/areas-thin-evidence.csv`：
- `evidence` 列区分三种空心：`mention_only`（只剩提及）/ `wrong_dropped`（原依据被判无关已解除）/ `none`（本来就没有）
- `mention_n` 是仍挂着的 mention 条数——有 mention 说明正文至少出现过地名，补采时优先按县找原文

    python scripts/list_thin_evidence_areas.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "qa" / "areas-thin-evidence.csv"
WRONG = ROOT / "reports" / "qa" / "link-wrong.csv"


def main() -> int:
    if not DB.exists():
        print(f"找不到 {DB}")
        return 1
    wrong: set[tuple[str, str]] = set()
    if WRONG.exists():
        with WRONG.open("r", encoding="utf-8-sig", newline="") as f:
            wrong = {(r["area_id"], r["policy_id"]) for r in csv.DictReader(f) if r.get("area_id")}

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    valid = "record_state='active' and status<>'待核'"
    rows = con.execute(
        f"""select a.area_id, a.name, a.province_code, a.county_code, a.status,
                   a.type_code, a.first_source_id,
                   sum(case when m.rel='mention' then 1 else 0 end) mention_n,
                   sum(case when m.rel in ('primary','support') then 1 else 0 end) hard_n,
                   count(m.policy_id) map_n
            from area a
            left join area_policy_map m on m.area_id=a.area_id and m.entity_type='area'
            where {valid}
            group by a.area_id
            having hard_n = 0
            order by a.province_code, a.county_code, a.area_id"""
    ).fetchall()

    regions = {r["region_code"]: r for r in con.execute("select region_code, name, short_name, level from region")}
    placed: dict[tuple[str, str], str] = {}
    for r in con.execute("select area_id, policy_id from area_policy_map where rel in ('primary','support')"):
        placed[(r["area_id"], r["policy_id"])] = r["policy_id"]

    out = []
    for r in rows:
        cty = regions.get(r["county_code"] or "")
        prov = regions.get(r["province_code"] or "")
        mention_only = (r["mention_n"] or 0) > 0
        out.append({
            "area_id": r["area_id"],
            "area_name": r["name"],
            "province": (prov["short_name"] or prov["name"]) if prov else r["province_code"],
            "county": cty["name"] if cty else (r["county_code"] or ""),
            "county_code": r["county_code"] or "",
            "type_code": r["type_code"] or "",
            "status": r["status"],
            "evidence": "mention_only" if mention_only else "none",
            "mention_n": r["mention_n"] or 0,
            "map_n": r["map_n"] or 0,
            "has_media_source": "Y" if r["first_source_id"] else "",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["area_id"])
        w.writeheader()
        w.writerows(out)

    print(f"{len(out)} 个片区无 primary/support 依据 -> {OUT.relative_to(ROOT)}")
    print("按省：" + "，".join(f"{k} {v}" for k, v in Counter(r["province"] for r in out).most_common()))
    print("按证据状态：" + "，".join(f"{k} {v}" for k, v in Counter(r["evidence"] for r in out).most_common()))
    print("按县 Top10：" + "，".join(f"{k} {v}" for k, v in Counter(r["county"] for r in out).most_common(10)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
