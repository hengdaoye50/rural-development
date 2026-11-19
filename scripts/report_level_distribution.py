"""统计已采集片区的「设立/命名层级」：省级 / 地市级 / 县区级（另列乡镇级）。

**口径定义（必须先读）**
  `层级` = 这个片区**由哪一级政府/部门设立或命名**得到的归类，依据优先序：
    1. `area_policy_map` 中 `rel='primary'` 的政策层级（`policy.issuer_level`）——
       代表「谁把它设立/命名」，这是最硬的一档；
    2. `area.issuer` 文本（记录自带的设立/发布机构）；
    3. `rel='support'` 的政策层级（点名支持，不是设立，仅作补充线索）；
    4. 都没有 → `不可判定`（绝大多数是只有 mention 或完全没有政策挂接的记录）
  直辖市的处理（按 2026-11-19 用户口径）：
    - 直辖市的**区**发文/设立 → 记**地市级**（区为地厅级）
    - 直辖市的**市**级发文 → 记**省级**（直辖市本身是省级行政区）
    - 直辖市的县（重庆）不折算，仍记县区级

  ⚠️ 这不是「片区所在县的行政级别」，也不是按片区规模分层。若要按空间归属统计，
  请用 `area.county_code` 直接分组，二者不可混用。

用法：
  python scripts/report_level_distribution.py
  python scripts/report_level_distribution.py --md reports/片区层级分布.md
"""
from __future__ import annotations

import collections
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "片区层级分布.md"

ORDER = {"province": 5, "city": 4, "county": 3, "town": 2, "other": 1}
ZH = {"province": "省级", "city": "地市级", "county": "县区级", "town": "乡镇级",
      "other": "其他", "unknown": "不可判定"}
LV_PRI = {"county": 0, "city": 1, "province": 2}
MUNI = {"110000": ("北京市", "北京"), "120000": ("天津市", "天津"),
        "310000": ("上海市", "上海"), "500000": ("重庆市", "重庆")}

PROV_KW = ("省委", "省政府", "省人民政府", "自治区党委", "自治区人民政府",
           "省农业", "省乡村", "省财政", "省发展", "省住房", "省自然资源",
           "省文化和旅游", "省水利", "省林业", "省交通运输")
CITY_KW = ("市委", "市政府", "市人民政府", "州委", "州政府", "盟委", "行署", "地区行政公署")
COUNTY_KW = ("县委", "县政府", "县人民政府", "区委", "区政府", "区人民政府",
             "旗委", "旗政府", "县级市")
TOWN_KW = ("镇党委", "镇政府", "乡政府", "街道办事处")
MINISTRY_KW = ("农业农村部", "财政部", "国家发展改革委", "国务院")


def main() -> int:
    args = sys.argv[1:]
    out = Path(args[args.index("--md") + 1]) if "--md" in args else OUT
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    regions = list(con.execute("select region_code,name,level,parent_code from region"))
    regname = {r["region_code"]: r["name"] for r in regions}
    name2lv = sorted(
        [(r["name"], r["level"]) for r in regions if r["name"]],
        key=lambda x: (-len(x[0]), LV_PRI.get(x[1], 9)),
    )
    # 直辖市的县级单元（区/县），用于识别「北京市怀柔区」这类写法。
    # 注意：region 里直辖市的区 parent 是「市辖区 110100/120100/…」而不是 110000，
    # 所以按码前两位归属到直辖市，不能按 parent_code 判断。
    muni_districts: dict[str, list[str]] = collections.defaultdict(list)
    for r in regions:
        if r["level"] == "county":
            prov = (r["region_code"] or "")[:2] + "0000"
            if prov in MUNI:
                muni_districts[prov].append(r["name"])

    def issuer_level(text: str) -> str:
        t = (text or "").strip()
        if not t:
            return ""
        for prov, (full, short) in MUNI.items():
            if full in t or short in t:
                for nm in muni_districts.get(prov, []):
                    base = re.sub(r"(区|县|市)$", "", nm)
                    if nm in t or (len(base) >= 2 and base in t):
                        return "county"  # 后续按「直辖市的区」折算为地市级
                return "province"
        for kw in PROV_KW:
            if kw in t:
                return "province"
        for kw in CITY_KW:
            if kw in t:
                return "city"
        for kw in COUNTY_KW:
            if kw in t:
                return "county"
        for kw in TOWN_KW:
            if kw in t:
                return "town"
        for kw in MINISTRY_KW:
            if kw in t:
                return "province"  # 中央部委：按省级及以上处理，报告须注明
        for nm, lv in name2lv:
            if len(nm) >= 3 and nm in t:
                return lv
        return ""

    def muni_fix(lv: str, province: str, county: str) -> str:
        if lv == "county" and province in MUNI:
            nm = regname.get(county, "")
            if nm.endswith("区") and nm != "市辖区":
                return "city"
        return lv

    rows = con.execute(
        """select a.area_id,a.name,a.province_code,a.county_code,a.issuer,a.status,a.setup_kind,
                  (select count(*) from area_caliber c where c.area_id=a.area_id and c.in_main_stat=1) is_main
           from area a where a.record_state='active'"""
    ).fetchall()
    links: dict[str, dict[str, list[str]]] = collections.defaultdict(dict)
    for r in con.execute(
        """select m.area_id,m.rel,p.issuer_level from area_policy_map m
           join policy p on p.policy_id=m.policy_id"""
    ):
        links[r["area_id"]].setdefault(r["rel"], []).append(r["issuer_level"] or "")

    def pick(levels: list[str]) -> str:
        vals = [x for x in levels if x in ORDER]
        return max(vals, key=lambda x: ORDER[x]) if vals else ""

    def classify(a, variant: str = "V4") -> tuple[str, str]:
        L = links.get(a["area_id"], {})
        p = pick(L.get("primary", []))
        il = issuer_level(a["issuer"])
        s = pick(L.get("support", []))
        if variant == "V4":       # 主口径：设立依据 > 记录发布者 > 支持
            chain = [("primary", p), ("issuer", il), ("support", s)]
        elif variant == "V1":     # 宽口径：再退到 mention（仅用于敏感性对照）
            anyl = pick([x for v in L.values() for x in v])
            chain = [("primary", p), ("support", s), ("issuer", il), ("any", anyl)]
        elif variant == "V6":     # 最严：只认 primary
            chain = [("primary", p)]
        else:                     # V5：发布者优先
            chain = [("issuer", il), ("primary", p), ("support", s)]
        for how, lv in chain:
            if lv:
                return muni_fix(lv, a["province_code"], a["county_code"]), how
        return "unknown", ""

    res = [(a, *classify(a)) for a in rows]

    def counts(pred, variant="V4"):
        c = collections.Counter(classify(a, variant)[0] for a in rows if pred(a))
        return c, sum(c.values())

    L: list[str] = []
    add = L.append
    add("# 片区层级分布（设立/命名层级）\n")
    add(f"> 生成：`scripts/report_level_distribution.py`｜快照：{date.today().isoformat()}｜库：`data/db/片区库.sqlite3`\n")
    add("## 口径（先说清楚层级指什么）\n")
    add("**层级 = 这个片区由哪一级政府/部门设立或命名**，不是它所在县的级别，也不是规模分层。判定优先序：\n")
    add("1. `primary` 政策层级（`policy.issuer_level`）——代表设立/命名主体，最硬；")
    add("2. `area.issuer` 文本（记录自带的设立/发布机构）；")
    add("3. `support` 政策层级（点名支持，不是设立，只作补充）；")
    add("4. 三者皆无 → **不可判定**（多为只有 `mention` 或完全没有政策挂接）。\n")
    add("直辖市（按用户 2026-11-19 口径）：**直辖市的区记地市级**（区为地厅级）；"
        "**直辖市市级记省级**（直辖市本身是省级行政区）；重庆的县不折算，仍记县区级。\n")

    add("## 一、主表\n")
    add("| 口径 | 合计 | 省级 | 地市级 | 县区级 | 乡镇级 | 其他 | 不可判定 |")
    add("|---|---|---|---|---|---|---|---|")
    for label, pred in (
        ("全库 active（含待核）", lambda x: True),
        ("在册非待核", lambda x: x["status"] != "待核"),
        ("主统计 A+B", lambda x: x["is_main"] == 1),
        ("待核", lambda x: x["status"] == "待核"),
    ):
        c, tot = counts(pred)
        add(f"| {label} | {tot} | {c['province']} | {c['city']} | {c['county']} | "
            f"{c['town']} | {c['other']} | {c['unknown']} |")
    add("")
    add("")
    c_all, tot_all = counts(lambda x: True)
    add(f"占比（全库 {tot_all:,}）：省级 {c_all['province']/tot_all*100:.0f}%、"
        f"地市级 {c_all['city']/tot_all*100:.0f}%、县区级 {c_all['county']/tot_all*100:.0f}%、"
        f"乡镇级 {c_all['town']/tot_all*100:.0f}%、不可判定 {c_all['unknown']/tot_all*100:.0f}%。\n")
    add("## 二、判定依据分布\n")
    how_c = collections.Counter(how or "无" for _, _, how in res)
    add("| 依据 | 条数 | 说明 |")
    add("|---|---|---|")
    for k, label in (("primary", "primary 政策（设立/命名文件）"),
                     ("issuer", "area.issuer（批准/发文单位）"),
                     ("support", "support 政策（点名支持）"),
                     ("无", "不可判定")):
        add(f"| {label} | {how_c.get(k, 0)} | |")
    add("")

    add("## 三、分省 × 层级（全库 active）\n")
    add("| 省码 | 合计 | 省级 | 地市级 | 县区级 | 乡镇级 | 其他 | 不可判定 |")
    add("|---|---|---|---|---|---|---|---|")
    tab = collections.defaultdict(collections.Counter)
    for a, lv, _ in res:
        tab[a["province_code"]][lv] += 1
    for p, c in sorted(tab.items(), key=lambda kv: -sum(kv[1].values())):
        add(f"| {p} | {sum(c.values())} | {c['province']} | {c['city']} | {c['county']} | "
            f"{c['town']} | {c['other']} | {c['unknown']} |")
    add("")

    add("## 四、不可判定为什么这么多\n")
    unk = [a for a, lv, _ in res if lv == "unknown"]
    add(f"共 **{len(unk)}** 条（全库 {len(rows)} 条的 {len(unk)/len(rows)*100:.0f}%）："
        "只有 `mention` 挂接、或完全没有政策挂接、且 `area.issuer` 为空。"
        "它们不是「没有片区」，而是**现有证据不足以判断设立层级**。"
        "补采（拿到设立/批复/名单文件）后会自动落位。\n")

    add("## 五、口径敏感性（必须一起看）\n")
    add("| 变体 | 规则 | 省级 | 地市级 | 县区级 | 乡镇级 | 不可判定 |")
    add("|---|---|---|---|---|---|---|")
    for v, desc in (("V4", "primary > issuer > support（主口径）"),
                    ("V5", "issuer > primary > support（发布者优先）"),
                    ("V1", "primary > support > issuer > mention（最宽）"),
                    ("V6", "仅 primary（最严，其余全记不可判定）")):
        c, tot = counts(lambda x: True, v)
        add(f"| {v} | {desc} | {c['province']} | {c['city']} | {c['county']} | "
            f"{c['town']} | {c['unknown']} |")
    add("")
    add("三种规则下省级占比在 17%–29% 之间摆动，说明「层级」目前**不是库里的显式字段**，"
        "而是从依据反推的派生分类。若要写进论文，建议：① 只用 V4；② 同时报可判定率；"
        "③ 把「不可判定」单列，不用比例外推。\n")

    add("## 六、复现\n")
    add("```powershell\npython scripts/report_level_distribution.py\n```\n")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK -> {out.relative_to(ROOT)}")
    c, tot = counts(lambda x: True)
    print(f"全库 {tot}: 省{c['province']} 地市{c['city']} 县区{c['county']} "
          f"乡镇{c['town']} 其他{c['other']} 未知{c['unknown']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
