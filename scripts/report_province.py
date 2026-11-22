# -*- coding: utf-8 -*-
"""单个省的数据档案（只读）：用于质量抽查。

输出：总量与口径、类型/设立方式/层级、年份、覆盖县、名单台账、证据与快照状态，
以及**逐条片区清单**（含县、状态、口径组、证据、政策数、来源快照是否可查）。

用法：
  python scripts/report_province.py 610000
  python scripts/report_province.py 陕西          # 可用省名
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = max((ROOT / "data" / "db").glob("*.sqlite3"), key=lambda p: p.stat().st_size)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    key = sys.argv[1].strip()
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row

    if key.lower().endswith("0000") and key.isdigit():
        code = key
    else:
        r = con.execute("select region_code from region where level='province' and name like ?",
                        (f"%{key}%",)).fetchone()
        if not r:
            print("找不到省：", key)
            return 1
        code = r[0]
    pname = con.execute("select name from region where region_code=?", (code,)).fetchone()[0]
    print(f"# {pname}（{code}）数据档案\n")

    q = lambda s, p=(): con.execute(s, p).fetchone()[0]  # noqa: E731
    active = q("select count(*) from area where province_code=? and record_state='active'", (code,))
    pend = q("select count(*) from area where province_code=? and record_state='active' and status='待核'", (code,))
    print(f"- 在册 active **{active}**（待核 {pend}、非待核 {active - pend}）")
    main_n = q("""select count(*) from area_caliber c join area a on a.area_id=c.area_id
                  where c.in_main_stat=1 and a.province_code=?""", (code,))
    wide_n = q("""select count(*) from area_caliber c join area a on a.area_id=c.area_id
                  where c.in_scope=1 and c.caliber_group in ('A','B','C') and a.province_code=?""", (code,))
    print(f"- 主统计 **{main_n}**｜宽统计 **{wide_n}**")
    groups = con.execute("""select c.caliber_group g, count(*) n from area_caliber c
        join area a on a.area_id=c.area_id where a.province_code=? and a.record_state='active'
        group by 1 order by 1""", (code,)).fetchall()
    print("- 五组：" + "｜".join(f"{g['g']} {g['n']}" for g in groups))
    n_belt = q("select count(*) from belt where province_code=?", (code,))
    n_pol = q("select count(*) from policy where province_code=?", (code,))
    n_src = q("""select count(*) from source where area_id in
                 (select area_id from area where province_code=?)""", (code,))
    print(f"- belt（象征单元）：{n_belt}｜policy：{n_pol}｜source：{n_src}")
    cov = q("select count(distinct county_code) from area where province_code=? and record_state='active'", (code,))
    tot = q("select count(*) from region where parent_code like ? and level='county'", (code[:2] + "%",))
    print(f"- 覆盖县：**{cov}** / {tot}")
    types = {r["t"]: r["n"] for r in con.execute(
        "select type_code t,count(*) n from area where province_code=? and record_state='active' group by 1",
        (code,))}
    setups = {r["k"]: r["n"] for r in con.execute(
        """select coalesce(nullif(setup_kind,''),'unknown') k,count(*) n from area
           where province_code=? and record_state='active' group by 1""", (code,))}
    print(f"- 类型：{types}")
    print(f"- 设立方式：{setups}")

    pr = con.execute("select roster_name, official_count, in_db_count, status, note from province_roster where province_code=?", (code,)).fetchone()
    if pr:
        print(f"- 省级台账：{pr['status']}｜官方数 {pr['official_count']}｜库内 {pr['in_db_count']}｜{pr['roster_name']}")
        if pr["note"]:
            print(f"  - note：{pr['note'][:160]}")
    cities = con.execute("""select r.name, c.status, c.official_count, c.in_db_count from city_roster c
        join region r on r.region_code=c.city_code where c.province_code=? order by c.city_code""", (code,)).fetchall()
    if cities:
        print("- 市级台账：" + "；".join(f"{c['name']}={c['status']}({c['in_db_count']}/{c['official_count']})" for c in cities))

    print("\n## 逐条清单\n")
    print("| area_id | 名称 | 县 | 状态 | 组 | 主统计 | 依据 | 政策数 | 快照 |")
    print("|---|---|---|---|---|---|---|---|---|")
    rows = con.execute("""
        select a.area_id, a.name, a.county_code, a.status, c.caliber_group g, c.in_main_stat m,
               coalesce(a.setup_kind,'unknown') sk,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel in ('primary','support')) npol,
               (select count(*) from area_policy_map p where p.area_id=a.area_id and p.rel='mention') nmen,
               (select count(*) from source s join area_source_map x on x.source_id=s.source_id
                 where x.area_id=a.area_id and coalesce(s.local_path,'')<>'') nsnap,
               (select count(*) from source s join area_source_map x on x.source_id=s.source_id
                 where x.area_id=a.area_id) nsrc
        from area a left join area_caliber c on c.area_id=a.area_id
        where a.province_code=? and a.record_state='active'
        order by a.county_code, a.area_id""", (code,)).fetchall()
    for a in rows:
        ev = "primary/support" if a["npol"] else ("仅 mention" if a["nmen"] else "无")
        print(f"| {a['area_id']} | {a['name']} | {a['county_code']} | {a['status']} | {a['g']} | "
              f"{'✓' if a['m'] else ''} | {ev} | {a['npol']} | {a['nsnap']}/{a['nsrc']} |")

    # 质量旗标
    print("\n## 质量旗标\n")
    thin = [a for a in rows if not a["npol"]]
    if thin:
        print(f"- 无 primary/support 依据：{len(thin)} 条 → " + "、".join(f"{a['name']}({a['area_id']})" for a in thin[:8]))
    nosnap = [a for a in rows if a["nsrc"] and a["nsnap"] < a["nsrc"]]
    if nosnap:
        print(f"- 有来源但缺本地快照：{len(nosnap)} 条")
    if pend:
        print(f"- 待核 {pend} 条不计入主统计")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
