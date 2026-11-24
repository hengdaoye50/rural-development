# -*- coding: utf-8 -*-
"""2022+ 体检落地：28 条年份无出处者置「不详」；抬头见喜合并到德城区。

--dry-run 只打印。
"""
import csv
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(".")
BP = ROOT / "data/clean/by_province"
DRY = "--dry-run" in sys.argv
c = sqlite3.connect("data/db/片区库.sqlite3")
c.row_factory = sqlite3.Row

rows = [dict(r) for r in c.execute("""
  select a.area_id, a.name, a.province_code, a.founded_ymd
  from area a where a.record_state='active' and a.founded_ymd >= '2022'""")]


def year_ok(aid: str, year: str) -> bool:
    for s in c.execute("""select s.title,s.published_ymd,s.local_path from area_source_map m
                          join source s on s.source_id=m.source_id where m.area_id=?""", (aid,)):
        if (s["published_ymd"] or "").startswith(year) or year in (s["title"] or ""):
            return True
        if s["local_path"] and (ROOT / s["local_path"]).exists():
            t = (ROOT / s["local_path"]).read_text(encoding="utf-8")
            i = t.find(year)
            while i >= 0:
                seg = t[max(0, i - 40): i + 50]
                if not any(k in seg for k in ("ICP", "备案", "许可证")):
                    return True
                i = t.find(year, i + 1)
    for p in c.execute("""select p.title,p.doc_no,p.issued_ymd,p.published_ymd from area_policy_map m
                          join policy p on p.policy_id=m.policy_id where m.area_id=?""", (aid,)):
        if (p["issued_ymd"] or p["published_ymd"] or "").startswith(year):
            return True
        if year in ((p["title"] or "") + (p["doc_no"] or "")):
            return True
    return False


missing = [r["area_id"] for r in rows if not year_ok(r["area_id"], r["founded_ymd"][:4])]
print(f"年份无出处 {len(missing)} 条：", ", ".join(missing))

if not DRY:
    today = date.today().isoformat()
    hit = 0
    for p in sorted(BP.glob("*-area.csv")):
        rd = list(csv.DictReader(p.open(encoding="utf-8-sig")))
        hdr = list(rd[0].keys()) if rd else []
        ch = False
        for r in rd:
            if r["area_id"] in missing:
                r["founded_ymd"] = ""
                r["founded_precision"] = "unknown"
                r["updated_at"] = today
                ch = True
                hit += 1
        if ch:
            tmp = p.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=hdr, lineterminator="\r\n")
                w.writeheader()
                w.writerows([{k: r.get(k, "") for k in hdr} for r in rd])
            tmp.replace(p)
            print("  已改", p.name)
    print("共改", hit, "条")
