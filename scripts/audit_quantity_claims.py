"""库内数量声明盘点：同一省、同一计量词，各文件说出的 N 值。

重要限制（2026-11 实测得出，别再指望它做截断检测）：
  按「省 + 计量词」分组会把大量**合法的不同口径**混在一起——
  山东的「10 个片区」是潍坊市域、「64 个片区」是省域；
  浙江重点村组团片区的 200/226/300/500 分别是不同年份的目标值与进展值。
  它们不是矛盾，是辖区与年份不同。
  要真正判断矛盾，必须解析「批次 + 年份 + 辖区」，本脚本不做这件事。

  更要紧的是：**广西 P450007 那种截断，库内交叉核验也抓不到**。
  实测广西 9 份文件命中冲突组合 0 个——库里只有那一份名单，
  没有第二个独立来源去说「应有 16 个」。外部核验必须真的去外部采集。

所以本脚本的定位是**盘点工具**（看某省有哪些数量口径、谁在说），
不是质量闸门。

抓取模式：`N个/条/处 + 计量词`。

用法：
  python scripts/audit_quantity_claims.py
  python scripts/audit_quantity_claims.py --csv reports/qa/quantity-claims.csv
  python scripts/audit_quantity_claims.py --province 450000
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

PROV = {
    "110000": "北京", "120000": "天津", "130000": "河北", "140000": "山西",
    "150000": "内蒙古", "210000": "辽宁", "220000": "吉林", "230000": "黑龙江",
    "310000": "上海", "320000": "江苏", "330000": "浙江", "340000": "安徽",
    "350000": "福建", "360000": "江西", "370000": "山东", "410000": "河南",
    "420000": "湖北", "430000": "湖南", "440000": "广东", "450000": "广西",
    "460000": "海南", "500000": "重庆", "510000": "四川", "520000": "贵州",
    "530000": "云南", "540000": "西藏", "610000": "陕西", "620000": "甘肃",
    "630000": "青海", "640000": "宁夏", "650000": "新疆",
}

COUNTERS = [
    "田园综合体", "片区组团", "组团片区", "重点村组团片区", "示范片区",
    "样板片区", "重点片区", "精品片区", "示范带", "样板带", "先导区",
    "示范片", "片区",
]
CLAIM = re.compile(
    r"(\d{1,4})\s*(?:个|条|处)\s*(" + "|".join(sorted(COUNTERS, key=len, reverse=True)) + r")"
)


def main() -> int:
    out_csv = ""
    only_prov = ""
    if "--csv" in sys.argv:
        out_csv = sys.argv[sys.argv.index("--csv") + 1]
    if "--province" in sys.argv:
        only_prov = sys.argv[sys.argv.index("--province") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    sql = ("SELECT policy_id, province_code, issuer_level, title, local_path "
           "FROM policy")
    params: tuple = ()
    if only_prov:
        sql += " WHERE province_code=?"
        params = (only_prov,)
    rows = conn.execute(sql, params).fetchall()

    claims: dict[tuple[str, str], list[tuple[int, str, str, str]]] = defaultdict(list)
    for r in rows:
        body = ROOT / r["local_path"]
        if not body.exists():
            continue
        text = body.read_text(encoding="utf-8")
        seen = set()
        for m in CLAIM.finditer(text):
            n, word = int(m.group(1)), m.group(2)
            ctx = text[max(0, m.start() - 18): m.end() + 10].replace("\n", " ")
            key = (n, word, ctx)
            if key in seen:
                continue
            seen.add(key)
            claims[(r["province_code"], word)].append(
                (n, r["policy_id"], r["issuer_level"], ctx)
            )

    conflicts = []
    for (prov, word), items in sorted(claims.items()):
        values = sorted({i[0] for i in items})
        if len(values) < 2:
            continue
        # 省级口径优先：把省/市级与县级分开看
        top = [i for i in items if i[2] in ("province", "city")]
        low = [i for i in items if i[2] not in ("province", "city")]
        top_vals = sorted({i[0] for i in top})
        conflicts.append({
            "province": PROV.get(prov, prov),
            "counter": word,
            "all_values": "/".join(str(v) for v in values),
            "top_values": "/".join(str(v) for v in top_vals) or "（无省市口径）",
            "n_claims": len(items),
            "detail": items,
        })

    conflicts.sort(key=lambda c: (-len(c["all_values"].split("/")), -c["n_claims"]))

    print(f"扫过 {len(rows)} 份政策；出现数量声明冲突的 (省, 计量词) 组合：{len(conflicts)}\n")
    for c in conflicts[:18]:
        print(f"[{c['province']}] {c['counter']:<12} 出现过 {c['all_values']:<18} "
              f"省级/市级口径 {c['top_values']}")
        shown = 0
        for n, pid, lv, ctx in sorted(c["detail"], key=lambda x: x[2] != "province"):
            if shown >= 4:
                break
            print(f"    {n:<5} {pid} [{lv}] …{ctx[:52]}…")
            shown += 1
        print()

    if out_csv:
        p = ROOT / out_csv
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["province", "counter", "n_value", "policy_id", "issuer_level", "context"])
            for c in conflicts:
                for n, pid, lv, ctx in c["detail"]:
                    w.writerow([c["province"], c["counter"], n, pid, lv, ctx])
        print(f"明细 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
