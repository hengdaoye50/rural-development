"""宏观层分省统计（`docs/01` §11 M 层）：各省有多少个片区化命名单元。

用途：看各省的量级与分布广度，做粗略的省际比较。
**不是**「片区化发展水平」指标——M 层完整度由采集覆盖决定，不是由现实决定。
故本报告强制与「县覆盖率」并列输出，缺一即为误导。

    python scripts/report_macro_layer.py        # -> reports/宏观层-分省数量.md
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
OUT = ROOT / "reports" / "宏观层-分省数量.md"


def main() -> int:
    if not DB.exists():
        print(f"找不到 {DB}")
        return 1
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    prov = {r["region_code"]: (r["short_name"] or r["name"]) for r in con.execute(
        "select region_code, name, short_name from region where level='province'")}
    cty_total = {r["p"]: r["n"] for r in con.execute(
        "select substr(region_code,1,2) || '0000' p, count(*) n from region "
        "where level='county' group by 1")}

    rows = con.execute(
        """select m.province_code p,
                  sum(case when m.kind='area' then 1 else 0 end) n_area,
                  sum(case when m.kind='belt' then 1 else 0 end) n_belt,
                  count(*) n_unit,
                  sum(case when m.kind='area' and m.has_hard=1 then 1 else 0 end) n_hard,
                  sum(case when m.kind='area' and m.status='待核' then 1 else 0 end) n_pending,
                  count(distinct m.county_code) n_cty
           from macro_unit m group by m.province_code"""
    ).fetchall()
    p_layer = {r["p"]: r["n"] for r in con.execute(
        "select province_code p, count(*) n from area_caliber "
        "where in_main_stat=1 group by province_code")}

    tot = {"n_area": 0, "n_belt": 0, "n_unit": 0, "n_hard": 0, "n_pending": 0, "n_cty": 0}
    lines = [
        "# 宏观层：分省片区化命名单元数量",
        "",
        "> 生成：`scripts/report_macro_layer.py`｜口径：`docs/01` §11 M 层｜快照见 `build_meta.built_at`",
        "",
        "## 怎么读这张表",
        "",
        "**M 层只放宽证据强度，不放宽对象类型。** 媒体稿命名、无政策依据、成立时间不详的单元都收；",
        "但示范县/镇/村、纯园区景区、城市控规分区仍然不收。",
        "",
        "**这一列数不等于「该省有多少个片区」。** 它等于「我们采到了多少个」——",
        "青海 3 个不代表青海只有 3 个。所以本表强制并列「县覆盖率」，单独看数量列即为误读。",
        "",
        "| 省份 | 实体片区 | 象征单元 | 命名单元合计 | 其中严口径有依据 | 待核 | 有单元县/总县 | 县覆盖率 | P 层主统计 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: -x["n_unit"]):
        p = r["p"]
        name = prov.get(p) or p
        tct = cty_total.get(p, 0)
        cov = f"{r['n_cty']}/{tct}" if tct else str(r["n_cty"])
        rate = f"{r['n_cty'] / tct * 100:.0f}%" if tct else "—"
        lines.append(
            f"| {name} | {r['n_area']} | {r['n_belt']} | **{r['n_unit']}** | {r['n_hard']} | "
            f"{r['n_pending']} | {cov} | {rate} | {p_layer.get(p, 0)} |")
        for k in tot:
            tot[k] += r[k]
    tct_all = sum(cty_total.values())
    lines.append(
        f"| **全国** | **{tot['n_area']}** | **{tot['n_belt']}** | **{tot['n_unit']}** | "
        f"**{tot['n_hard']}** | **{tot['n_pending']}** | **{tot['n_cty']}/{tct_all}** | "
        f"**{tot['n_cty'] / tct_all * 100:.1f}%** | **{sum(p_layer.values())}** |")

    # 去重掉的跨表重名（按省），说明 M 层合计为何小于两表之和
    dedup = {r["p"]: r["n"] for r in con.execute(
        """select b.province_code p, count(*) n from belt b
           join area a on a.province_code=b.province_code and a.name_norm=b.name_norm
                       and a.record_state='active'
           where b.record_state='active' group by b.province_code""")}

    ranked = sorted(rows, key=lambda x: -x["n_unit"])
    top3 = "、".join(f"{prov.get(r['p']) or r['p']} {r['n_unit']}" for r in ranked[:3])
    bottom5 = "、".join(f"{prov.get(r['p']) or r['p']} {r['n_unit']}" for r in ranked[-5:])
    belt_top = "、".join(
        f"{prov.get(r['p']) or r['p']} {r['n_belt']}"
        for r in sorted(rows, key=lambda x: -x["n_belt"])[:3] if r["n_belt"])
    dedup_note = "，".join(f"{prov.get(p) or p} 去重 {n} 条" for p, n in dedup.items()) or "无"

    lines += [
        "",
        "## 三个门槛依次收紧",
        "",
        "| 层 | 数量 | 含义 |",
        "|---|---|---|",
        f"| M 命名单元 | {tot['n_unit']} | 有一条线索即收，含待核与媒体来源；只用于看量级与分布 |",
        f"| 有 primary/support 依据的实体片区 | {tot['n_hard']} | 正文点名支撑；仍含时间不详 |",
        f"| P 主统计 | {sum(p_layer.values())} | 时间窗内 + 有依据 + `setup_kind` 分列；政策分析只能用这个 |",
        "",
        "跨层相减没有意义：M − P 的差额不是「质量差的片区」，而是「证据强度不足但确实被这样称呼的单元」。",
        "",
        "## 省际观察（仅描述量级，不作解释）",
        "",
        f"- 量级前三：{top3}——与「省级名单最厚 + 采集最久」一致，不能反过来当发展水平证据",
        f"- 量级最低五位：{bottom5}——这些省的共同点是**没有公开省级名单**，属采集缺口而非实践缺口，",
        "  写报告必须标注",
        f"- 去重后象征单元前三：{belt_top}——这是各省组织形态差异（有的省以「带」为主要载体），",
        "  不该视为「片区化程度低」",
        f"- 跨表重名去重情况：{dedup_note}。同一单元被同时在 `area` 与 `belt` 各记一次，",
        "  M 层保留 `area` 那条；这不是数据错误，是两表并行登记的历史产物",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"M 层命名单元 {tot['n_unit']}（area {tot['n_area']} + belt {tot['n_belt']} − 跨表重名）"
          f"｜有依据 {tot['n_hard']}｜P 层主统计 {sum(p_layer.values())}")
    print(f"OK -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
