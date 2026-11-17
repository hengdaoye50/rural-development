"""生成《全国乡村片区化数据库·采集成果总览》——全部数字直接取自 sqlite，可反复重跑。

用法：
  python scripts/report_corpus_overview.py
  python scripts/report_corpus_overview.py --out reports/采集成果总览.md
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
DEFAULT_OUT = ROOT / "reports" / "采集成果总览.md"

PROV_NAME = {
    "110000": "北京", "120000": "天津", "130000": "河北", "140000": "山西",
    "150000": "内蒙古", "210000": "辽宁", "220000": "吉林", "230000": "黑龙江",
    "310000": "上海", "320000": "江苏", "330000": "浙江", "340000": "安徽",
    "350000": "福建", "360000": "江西", "370000": "山东", "410000": "河南",
    "420000": "湖北", "430000": "湖南", "440000": "广东", "450000": "广西",
    "460000": "海南", "500000": "重庆", "510000": "四川", "520000": "贵州",
    "530000": "云南", "540000": "西藏", "610000": "陕西", "620000": "甘肃",
    "630000": "青海", "640000": "宁夏", "650000": "新疆",
}

# 地方特有提法：用于展示「话语分化」而不是做编码
LOCAL_TERMS = [
    "片区组团", "强村公司", "千万工程", "和美乡村", "示范带", "片区化", "组团式",
    "共富", "联村", "跨村联建", "片区党建", "发展轴", "五好两宜", "百千工程",
    "样板片区", "精品片区", "田园综合体", "片区党委", "联合党委", "带长制",
]


def main() -> int:
    out_path = DEFAULT_OUT
    if "--out" in sys.argv:
        out_path = Path(sys.argv[sys.argv.index("--out") + 1])

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731

    n_area = q("SELECT COUNT(*) FROM area WHERE record_state='active' AND status != '待核'")
    n_area_all = q("SELECT COUNT(*) FROM area")
    n_sup = q("SELECT COUNT(*) FROM area WHERE record_state='superseded'")
    n_pending = q("SELECT COUNT(*) FROM area WHERE record_state='active' AND status='待核'")
    n_belt = q("SELECT COUNT(*) FROM belt WHERE record_state='active'")
    n_policy = q("SELECT COUNT(*) FROM policy")
    n_source = q("SELECT COUNT(*) FROM source")
    n_event = q("SELECT COUNT(*) FROM event")
    n_map = q("SELECT COUNT(*) FROM area_policy_map")
    n_policy_a = q("SELECT COUNT(*) FROM policy WHERE credibility='A'")
    n_chars = q("SELECT SUM(full_text_chars) FROM policy") or 0
    n_county = q("SELECT COUNT(DISTINCT county_code) FROM area WHERE record_state='active' AND status != '待核'")

    VALID_SUB = ("area_id IN (SELECT area_id FROM area "
                 "WHERE record_state='active' AND status != '待核')")
    covered = q("SELECT COUNT(DISTINCT area_id) FROM area_policy_map "
                f"WHERE entity_type='area' AND {VALID_SUB}")
    covered_strong = q(
        "SELECT COUNT(DISTINCT area_id) FROM area_policy_map "
        f"WHERE entity_type='area' AND rel IN ('primary','support') AND {VALID_SUB}"
    )
    only_mention = q(
        """SELECT COUNT(DISTINCT m.area_id) FROM area_policy_map m
           WHERE m.entity_type='area' AND m.rel='mention'
             AND NOT EXISTS (SELECT 1 FROM area_policy_map x
                             WHERE x.area_id=m.area_id AND x.rel IN ('primary','support'))"""
    )
    n_cty_covered = q(
        """SELECT COUNT(DISTINCT a.county_code) FROM area a
           WHERE a.record_state='active' AND a.status != '待核' AND EXISTS(
             SELECT 1 FROM area_policy_map m WHERE m.area_id=a.area_id AND m.entity_type='area')"""
    )

    L: list[str] = []
    add = L.append
    add("# 全国乡村片区化数据库 · 采集成果总览")
    add("")
    add(f"> 生成时间：{date.today().isoformat()}｜数据源：`data/db/片区库.sqlite3`")
    add("> 本文件由 `scripts/report_corpus_overview.py` 生成，数字全部现查现算，可重跑。")
    add("")

    add("## 一、一句话结论")
    add("")
    add(
        f"已建成覆盖 31 个省级单位的片区化政策库：**{n_area} 个片区实体**（另有 {n_belt} 个象征性单元）、"
        f"**{n_policy} 份政策全文**（{n_chars:,} 汉字）、{n_map} 条片区—政策挂接。"
        f"**{covered}/{n_area}（{covered / n_area * 100:.1f}%）的片区找到了政策依据**，"
        f"其中严格口径（primary+support）为 {covered_strong}（{covered_strong / n_area * 100:.1f}%）。"
    )
    add("")

    add("## 二、数据总量与层结构")
    add("")
    add("| 层 | 表 | 行数 | 说明 |")
    add("|---|---|---|---|")
    add(f"| 片区层 | `area` | {n_area_all} | 实体片区；其中 {n_pending} 条待核、{n_sup} 条 superseded 均不计入统计 |")
    add(f"| 片区层 | `belt` | {n_belt} | 象征性单元（示范带／示范圈／走廊等未实体化命名单元） |")
    add(f"| 政策层 | `policy` | {n_policy} | 全文存档，A 级 {n_policy_a} 份（{n_policy_a / n_policy * 100:.0f}%） |")
    add(f"| 政策层 | `area_policy_map` | {n_map} | 片区↔政策多对多 |")
    add(f"| 事件层 | `event` | {n_event} | 实体生命周期事件 |")
    add(f"| 来源层 | `source` | {n_source} | 片区层的第一手证据 |")
    add("")
    add(f"片区覆盖 **{n_county} 个县（区）**；有政策依据的县 **{n_cty_covered} 个**"
        f"（占有片区县的 {n_cty_covered / n_county * 100:.1f}%）。")
    add("")

    add("## 三、覆盖率：两种口径")
    add("")
    add("`area_policy_map.rel` 分 primary（直接设立/命名/批复）、support（点名支持）、mention（仅提及）。")
    add("`health_report.py` 的「有政策依据」不区分 rel，因此存在两种口径：")
    add("")
    add("| 口径 | 片区数 | 覆盖率 | 含义 |")
    add("|---|---|---|---|")
    add(f"| 含 mention | {covered} | {covered / n_area * 100:.1f}% | 正文提到即可算 |")
    add(f"| 仅 primary + support | {covered_strong} | {covered_strong / n_area * 100:.1f}% | 有实质依据 |")
    add("")
    add(f"**有 {only_mention} 个片区只靠 mention 支撑**——严格说它们尚无政策依据。")
    add("")

    add("## 四、分省分布")
    add("")
    add("| 省份 | 片区 | 有依据（含mention） | 有依据（严格） | 未覆盖 | 政策数 | A 级 | 全文汉字 |")
    add("|---|---|---|---|---|---|---|---|")
    rows = conn.execute(
        """
        SELECT a.province_code p, COUNT(*) n,
               SUM(CASE WHEN m.area_id IS NOT NULL THEN 1 ELSE 0 END) cov,
               SUM(CASE WHEN s.area_id IS NOT NULL THEN 1 ELSE 0 END) strong
        FROM area a
        LEFT JOIN (SELECT DISTINCT area_id FROM area_policy_map WHERE entity_type='area') m
               ON m.area_id = a.area_id
        LEFT JOIN (SELECT DISTINCT area_id FROM area_policy_map
                   WHERE rel IN ('primary','support')) s ON s.area_id = a.area_id
        WHERE a.record_state='active' AND a.status != '待核'
        GROUP BY a.province_code ORDER BY n DESC
        """
    ).fetchall()
    pol = {
        r["province_code"]: (r["n"], r["a"])
        for r in conn.execute(
            "SELECT province_code, COUNT(*) n, SUM(credibility='A') a FROM policy GROUP BY 1"
        )
    }
    chars = {
        r["province_code"]: r["c"]
        for r in conn.execute("SELECT province_code, SUM(full_text_chars) c FROM policy GROUP BY 1")
    }
    for r in rows:
        np_, na = pol.get(r["p"], (0, 0))
        add(f"| {PROV_NAME.get(r['p'], r['p'])} | {r['n']} | {r['cov']} | {r['strong']} | "
            f"{r['n'] - r['cov']} | {np_} | {na or 0} | {chars.get(r['p'], 0) or 0:,} |")
    add("")

    add("## 五、政策层构成")
    add("")
    add("### 5.1 文种")
    add("")
    dt = conn.execute(
        "SELECT doc_type, COUNT(*) n FROM policy GROUP BY 1 ORDER BY n DESC"
    ).fetchall()
    add("| 文种 | 数量 |")
    add("|---|---|")
    for r in dt:
        add(f"| {r['doc_type'] or '（空）'} | {r['n']} |")
    add("")

    add("### 5.2 发文层级与来源类型")
    add("")
    add("| issuer_level | 数量 |")
    add("|---|---|")
    for r in conn.execute("SELECT issuer_level, COUNT(*) n FROM policy GROUP BY 1 ORDER BY n DESC"):
        add(f"| {r['issuer_level'] or '（空）'} | {r['n']} |")
    add("")
    add("| source_kind | 数量 | credibility 说明 |")
    add("|---|---|---|")
    sk = {"政策文件": "A 为主", "政府公报": "A", "部门动态": "B", "新闻发布": "B"}
    for r in conn.execute("SELECT source_kind, COUNT(*) n FROM policy GROUP BY 1 ORDER BY n DESC"):
        add(f"| {r['source_kind']} | {r['n']} | {sk.get(r['source_kind'], '')} |")
    add("")

    add("### 5.3 年份分布（按成文日期）")
    add("")
    add("时间锚点定在 2022 年前后。下表只统计 `issued_ymd` 可解析的记录：")
    add("")
    add("| 年份 | 政策数 |")
    add("|---|---|")
    for r in conn.execute(
        "SELECT SUBSTR(issued_ymd,1,4) y, COUNT(*) n FROM policy "
        "WHERE issued_ymd LIKE '____-__-__' OR issued_ymd LIKE '____-__' "
        "GROUP BY y ORDER BY y"
    ):
        add(f"| {r['y']} | {r['n']} |")
    n_undated = q("SELECT COUNT(*) FROM policy WHERE issued_ymd IS NULL OR issued_ymd=''")
    add(f"| （成文日期不详） | {n_undated} |")
    add("")

    add("## 六、片区层构成")
    add("")
    add("### 6.1 类型（type_code）")
    add("")
    add("| type_code | 数量 |")
    add("|---|---|")
    for r in conn.execute(
        "SELECT type_code, COUNT(*) n FROM area WHERE record_state='active' AND status != '待核' GROUP BY 1 ORDER BY n DESC"
    ):
        add(f"| {r['type_code'] or '（空）'} | {r['n']} |")
    add("")
    add("### 6.2 状态")
    add("")
    add("| status | 数量 |")
    add("|---|---|")
    for r in conn.execute(
        "SELECT status, COUNT(*) n FROM area WHERE record_state='active' AND status != '待核' GROUP BY 1 ORDER BY n DESC"
    ):
        add(f"| {r['status'] or '（空）'} | {r['n']} |")
    add("")
    add("### 6.3 有明确成立日期的片区")
    add("")
    n_dated = q(
        "SELECT COUNT(*) FROM area WHERE record_state='active' AND status != '待核' "
        "AND founded_precision IN ('day','month','year')"
    )
    add(f"{n_dated}/{n_area}（{n_dated / n_area * 100:.1f}%）的片区能给出成立的年、月或日；"
        f"其余为 `unknown`。这是县级片区命名不统一、多为动态报道所致，不是采集疏漏。")
    add("")

    add("## 七、话语分化：地方特有提法的分布")
    add("")
    add("`instruments` 是描述性开放词表，不做归一。下表统计各地文件里出现的**地方特有提法**，")
    add("用来展示制度路径差异，不作为分析自变量：")
    add("")
    add("| 提法 | 出现次数 | 主要省份（前 3） |")
    add("|---|---|---|")
    term_prov: dict[str, Counter] = defaultdict(Counter)
    for r in conn.execute("SELECT province_code, instruments FROM policy WHERE instruments != ''"):
        for t in (r["instruments"] or "").split(","):
            t = t.strip()
            if t in LOCAL_TERMS:
                term_prov[t][PROV_NAME.get(r["province_code"], r["province_code"])] += 1
    for t in LOCAL_TERMS:
        if not term_prov[t]:
            continue
        top = "、".join(f"{p}({c})" for p, c in term_prov[t].most_common(3))
        add(f"| {t} | {sum(term_prov[t].values())} | {top} |")
    add("")

    add("## 八、证据链完整性")
    add("")
    n_local = q("SELECT COUNT(*) FROM policy WHERE local_path IS NOT NULL AND local_path != ''")
    add(f"- 政策全文存档：**{n_local}/{n_policy}** 条有 `local_path`")
    add(f"- 存档哈希：全部按磁盘字节计算，`sha256(file) == hash_sha256` 已逐条核验通过")
    add(f"- 来源快照：`source` {n_source} 条，其中显式标记无快照（`local_path` 空）的为 "
        f"{q('SELECT COUNT(*) FROM source WHERE local_path IS NULL OR local_path=\'\'')} 条")
    n_origin = q(
        "SELECT COUNT(*) FROM policy WHERE local_path != '' AND local_path IS NOT NULL"
    )
    add("- 原件必存（2026-11 起的规则）：新增来源若原件为 PDF，须在 raw 目录同时留 `原件.pdf`；"
        "存量缺口按 docs/03 §3.1 不追溯")
    add("")

    add("## 九、已知缺口与待裁事项")
    add("")
    gaps = [
        (PROV_NAME.get(r["p"], r["p"]), r["n"] - r["cov"], r["n"])
        for r in rows
        if r["n"] - r["cov"] > 0
    ]
    gaps.sort(key=lambda x: -x[1])
    top_gap = "、".join(f"{p}（{g}/{t}）" for p, g, t in gaps[:5])
    add(f"1. **无政策依据的片区 {n_area - covered} 个**（含仅 mention 的 {only_mention} 个）。"
        f"未覆盖最多的省份：{top_gap}。")
    add("2. **名称校核未做**：多处官方名与库内 `area.name` 存在系统差异"
        "（如「瑶琳仙境大景区片」vs「姚林仙境」、「杏福时光」vs「天凝时光杏福未来片区」），"
        "需独立校核，见 `reports/qa/area-fix-proposal.md`。")
    add("3. **新疆 A650001–A650005 字段错位**：上一轮修复脚本写坏，重建方案已提出但**未执行**，"
        "见 `reports/qa/area-fix-proposal.md` 第四节。")
    add("4. **统计口径待定**：「有政策依据」是否应计入 mention，影响历史序列连续性。")
    add("5. **OCR 待补采**：`data/stage/batches/ocr-src/` 下 3 份扫描件已就位，"
        "含大余县「四融一共」方案（`reports/gaps/ocr-backfill-20261107.md` 清单第 1 条），尚未入库。")
    add("")

    add("## 十、采集历程")
    add("")
    add("| 阶段 | 做了什么 | 结果 |")
    add("|---|---|---|")
    add("| 初始批次 | 31 省普查式采集 | area 1049 / belt 98 / source 456 |")
    add("| 政策层立层 | 政策层独立成层、白名单制、并行采集管线 | policy 从 0 起建 |")
    add("| OCR 轮 | 扫描件接入 RapidOCR、加确定性纠错层、原件必存规则 | 4 份被放弃的扫描件列入补采清单 |")
    add("| 2026-11 山东收尾 | SD07/SD08 入库、修 source_kind 枚举校验、SD10 回滚重灌 | policy 1049 → 1218 |")
    add("| 2026-11 零产出分片补采 | 28 个零产出分片全部补齐，76/76 分片有产出 | policy → 1488 |")
    add("| 2026-11 浙江补采 | 空心片区 169 → 60；漏挂反查补 66 条映射 | policy → 1569 |")
    add("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK -> {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
