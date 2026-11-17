"""执行 reports/qa/area-fix-proposal.md 中经人工确认的区划归属修正。

改动只写 data/clean/by_province/{ABBR}-{area,area_region_map}.csv，
再由 merge_by_province.py 覆盖根表——不直接改 data/clean/*.csv 与 sqlite。

每条 fix 自带 old → new，只有当前值仍等于 old 时才改，可反复重跑。
用法：
  python scripts/apply_area_fixes.py            # 执行
  python scripts/apply_area_fixes.py --dry-run  # 只看会改哪些行
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"

# area_id, 省缩写, 现 county_code, 应 county_code, 依据
FIXES: list[tuple[str, str, str, str, str]] = [
    ("A320077", "JS", "320114", "320117",
     "cover_desc 自述「溧水区无想山南麓」，320114 为雨花台区"),
    ("A360010", "JX", "360782", "360727",
     "360782 是 region 表里的占位码（name 等于代码本身），龙南市实为 360727"),
    ("A360019", "JX", "360727", "360726",
     "360727 被龙南占用后腾出的错位；安远县实为 360726"),
    ("A510016", "SC", "510681", "510682",
     "issuer 与 cover_desc 均指什邡市，510681 是广汉市；什邡为 510682"),
    ("A370178", "SD", "371522", "371521",
     "cover_desc 自述「阳谷县侨润街道春和八里」，371522 是莘县；阳谷县为 371521"),
    ("A140003", "SX", "140521", "140522",
     "summary 自述「县级代码按晋城辖域推定（阳城县）」；横河镇属阳城县 140522，"
     "SX01 采集到阳政办发〔2025〕1号「横河镇太行一号国家风景道旅游环线精品片区」"),
    ("A370066", "SD", "371321", "371323",
     "院东头镇属沂水县（371323），371321 是沂南县；SD09 采集按实际发文县填 371323，"
     "库内 cover_desc「沂南县院东头镇」系误认"),
    ("A510001", "SC", "510724", "510705",
     "四条均自述「绵阳市安州区」；510724 是 region 表占位码（name 等于代码），安州区为 510705"),
    ("A510002", "SC", "510724", "510705",
     "同上；蝴蝶谷在安州区"),
    ("A510003", "SC", "510724", "510705",
     "同上；猕猴桃产业融合发展片区属安州区"),
    ("A510004", "SC", "510724", "510705",
     "同上；现代优质粮油发展片区属安州区"),
    # ---- 2026-11 清洗：挂在 region 占位码（name 等于代码）上的 15 条 ----
    # 依据一律取自该条自身的 cover_desc/name，不推测
    ("A330160", "ZJ", "331021", "331083",
     "cover「以干江镇上栈头村为重点村」；干江镇属玉环市 331083，331021 为 region 占位码"),
    ("A330161", "ZJ", "331021", "331083",
     "cover「以清港镇垟根村为重点村」；清港镇属玉环市 331083"),
    ("A340009", "AH", "341822", "341882",
     "cover「新杭镇域，宣城市级乡村振兴示范片区，广德市三大重点片区之一」；广德市 341882"),
    ("A340010", "AH", "341822", "341882",
     "cover「卢村乡域」；卢村乡属广德市 341882"),
    ("A340011", "AH", "341822", "341882",
     "cover「东亭镇域」；东亭镇属广德市 341882"),
    ("A360001", "JX", "360782", "360783",
     "cover「以龙南为中心」；龙南市 2020 撤县设市后国标码为 360783，360782 为占位码"),
    ("A360010", "JX", "360727", "360783",
     "360727 是撤县设市前的龙南县旧码（region 表另存 360783 龙南市），统一到现行码"),
    ("A410002", "HA", "411626", "411603",
     "名称「淮阳区…」；淮阳区为 411603，411626 为占位码"),
    ("A500004", "CQ", "500126", "500155",
     "cover「重庆市梁平区东山特色片区」；梁平区 500155，500126 非国标有效码"),
    ("A500005", "CQ", "500126", "500155", "cover「重庆市梁平区西山特色片区」；梁平区 500155"),
    ("A500006", "CQ", "500126", "500155", "cover「重庆市梁平区平坝特色片区」；梁平区 500155"),
    ("A500007", "CQ", "500126", "500155",
     "cover「重庆市梁平区屏锦镇万年社区」；屏锦镇属梁平区 500155"),
    ("A500008", "CQ", "500126", "500155", "cover「重庆市梁平区西部百里竹海片区」；梁平区 500155"),
    ("A520016", "GZ", "520421", "520403",
     "cover「平坝区乐平镇大屯村」；平坝区 520403，520421 为占位码"),
    ("A520015", "GZ", "522322", "522302",
     "cover「兴仁市大山镇老里旗村」；兴仁市 522302，522322 为占位码"),
    ("A610002", "SN", "610521", "610503",
     "cover「华州区高塘镇渭华现代农业片区」；华州区 610503，610521 为占位码"),
]

# area_id, 省缩写, 现 city_code, 应 city_code, 依据（只改 area.city_code）
CITY_FIXES: list[tuple[str, str, str, str, str]] = [
    ("A370065", "SD", "371500", "371700",
     "县码 371724 为巨野县（属菏泽市 371700），371500 是聊城市；董官屯镇属巨野县"),
]

# area_id, 省缩写, 字段, 现值, 依据（清空被污染的数值字段，值多为道路编号或户数）
FIELD_CLEARS: list[tuple[str, str, str, str, str]] = [
    ("A320025", "JS", "scale_villages", "344", "cover「G344 国道 47 公里横跨 4 镇 15 村」——344 是国道编号，非村数"),
    ("A320051", "JS", "scale_villages", "611", "cover「沿 611 省道 15 个行政村」——611 是省道编号，非村数"),
    ("A320066", "JS", "scale_villages", "600", "cover 无此数，600 个行政村对一个片区不成立，待复核后回填"),
    ("A350009", "FJ", "scale_villages", "800余户", "户数不是村数，且字段须为整数，待复核"),
    ("A350029", "FJ", "scale_villages", "325", "cover 无此数，325 个行政村不成立，待复核后回填"),
    # ---- 2026-11 清洗第二批：validate 新增数值字段检查后浮出的同类污染 ----
    ("A320027", "JS", "scale_towns", "盐城市/盐都区", "地名写进了数值字段"),
    ("A320055", "JS", "scale_towns", "宜兴市", "地名写进了数值字段"),
    ("A320065", "JS", "scale_towns", "泰州市/兴化市", "地名写进了数值字段"),
    ("A330010", "ZJ", "scale_villages", "大港头一核带五村文旅融合", "片区名写进了数值字段；「一核带五村」不能确定是 5 村还是含核心村，待复核"),
    ("A330018", "ZJ", "scale_villages", "滨湖六村溇港农遗保护开发", "片区名写进了数值字段；「六村」是否为 6 个行政村待核原文"),
    ("A330028", "ZJ", "scale_villages", "滕头村及周边9村", "文本写进了数值字段；9 村是否含滕头村本身不明，待复核"),
    ("A350025", "FJ", "scale_towns", "3-5", "区间值不是确定数，待复核后填确定值"),
]

# area_id, 省缩写, 现 name, 应 name, 依据（只改 area.name 与 name_norm）
NAME_FIXES: list[tuple[str, str, str, str, str]] = [
    ("A650004", "XJ", "色也克镇乡村振兴示范片区", "色也克乡乡村振兴示范片区",
     "岳普湖县为 4 镇 5 乡，色也克是乡；2025-01 乡镇国土空间规划与泰安援疆报道均作「色也克乡」"),
    ("A330340", "ZJ", "好YOUNG田园片区", "好样田园片区",
     "官方文本（P330002 湖州样板片区名单）写作「好样田园片区」；库内混入拉丁大写属录入退化，不改实体"),
]

# 整行字段重建：上一轮 repair-2026-09 把若干列挤进了 tags，导致结构化字段变成垃圾值。
# 原值在 tags 里逐段完整保留（已逐行核对，无截断），因此按下表还原，不是推测。
# 结构：area_id -> (省缩写, {字段: 新值}, 依据)
# 护栏：仅当该行 created_by == 'repair-2026-09' 且 town_codes 仍是垃圾值时才执行，可反复重跑。
ROW_REBUILDS: dict[str, tuple[str, dict[str, str], str]] = {
    "A650001": ("XJ", {
        "tags": "党建;产业;和美乡村",
        "town_codes": "艾西曼镇",
        "cover_desc": "岳普湖县艾西曼镇「党建领航·田园牧歌」示范片区，10个行政村1.93万人，饲料加工厂/合作社孵化中心等",
        "scale_villages": "10",
        "scale_towns": "",
        "issuer": "泰安援疆指挥部/艾西曼镇党委",
        "summary": "艾西曼镇「党建领航·田园牧歌」乡村振兴示范片区位于岳普湖县西部，是岳普湖县5大乡村振兴示范片区中位置最西的片区。2023年以来泰安援疆指挥部以「党建领航、产业强基、和美增色」为创建思路，投入援疆资金3000余万，重点实施饲料加工厂、党支部领办合作社孵化中心等项目。2024年畜牧养殖饲料营养转化率由40%提升到85%以上。",
    }, "tags 残留段 0/1/2/3/4/6 分别还原为 tags/town_codes/cover_desc/scale_villages/issuer/summary"),
    "A650002": ("XJ", {
        "tags": "和美乡村",
        "town_codes": "也克先拜巴扎镇",
        "cover_desc": "岳普湖县也克先拜巴扎镇「和美乡村·幸福巴扎」示范片区，位于艾西曼片区以东",
        "scale_villages": "",
        "scale_towns": "",
        "issuer": "泰安援疆指挥部/也克先拜巴扎镇党委",
        "summary": "也克先拜巴扎镇「和美乡村·幸福巴扎」乡村振兴示范片区与艾西曼镇片区相接，同属岳普湖县5大乡村振兴示范片区。",
    }, "tags 残留段 0/1/2/5/6 还原；段 3、4 原为空"),
    "A650003": ("XJ", {
        "tags": "产业",
        "town_codes": "岳普湖乡",
        "cover_desc": "岳普湖乡无花果产业示范片区，新疆最大无花果标准种植基地，年加工无花果果酱450吨",
        "scale_villages": "",
        "scale_towns": "",
        "issuer": "泰安援疆指挥部/岳普湖乡党委",
        "summary": "岳普湖乡成功创建全国「一村一品」示范村镇，成为新疆最大的无花果标准种植基地；新建党建引领无花果加工合作社，探索「援疆企业+党支部+农户」运营模式，年可加工无花果果酱450吨。",
    }, "tags 残留段 0/1/2/4/5 还原"),
    "A650004": ("XJ", {
        "tags": "产业;文旅",
        "town_codes": "色也克乡",
        "cover_desc": "岳普湖县色也克镇乡村振兴示范片区，色也克镇百草园项目",
        "scale_villages": "",
        "scale_towns": "",
        "issuer": "泰安援疆指挥部/色也克镇党委",
        "summary": "沿省道S310连片打造的岳普湖县5大乡村振兴示范片区涉及岳普湖乡、艾西曼镇、色也克镇、铁热木镇等6个乡镇，色也克镇百草园为片区产业项目之一。",
    }, "tags 残留段 0/1/2/4/5 还原；cover_desc 与 summary 照原文保留「色也克镇」（引文不改），仅 town_codes 用规范建制「乡」"),
    "A650005": ("XJ", {
        "tags": "产业",
        "town_codes": "铁热木镇",
        "cover_desc": "岳普湖县铁热木镇乡村振兴示范片区，全国小茴香绿色食品原料基地",
        "scale_villages": "",
        "scale_towns": "",
        "issuer": "泰安援疆指挥部/铁热木镇党委",
        "summary": "铁热木镇成功申报农业农村部「全国小茴香绿色食品原料基地」认证；岳普湖县乡村振兴示范片区打造项目被评为「山东援疆出色项目」。",
    }, "tags 残留段 0/1/2/4/5 还原"),
}

# 重建后统一清掉没有原文支撑的占位日期与垃圾时间戳
# docs/02：未知日期留空，不猜
ROW_REBUILD_CLEAR = {"founded_ymd": "", "founded_precision": "unknown"}
BATCH_TIMESTAMP = "2026-09-30T12:00:00+08:00"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        return list(rows[0].keys()) if rows else [], rows


def _write(path: Path, cols: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    dry = "--dry-run" in sys.argv
    changed = 0
    for area_id, abbr, old, new, why in FIXES:
        for table, col in (("area", "county_code"), ("area_region_map", "region_code")):
            path = BY_PROV / f"{abbr}-{table}.csv"
            cols, rows = _read(path)
            hit = [r for r in rows if r.get("area_id") == area_id and r.get(col) == old]
            if not hit:
                stale = [r.get(col) for r in rows if r.get("area_id") == area_id]
                print(f"  跳过 {area_id} {table}: 无 {old} 行（现值 {stale}）")
                continue
            for r in hit:
                r[col] = new
            changed += len(hit)
            print(f"  {area_id} {table}: {old} -> {new}  ({why})")
            if not dry:
                _write(path, cols, rows)
    print(f"{'dry-run，' if dry else ''}共改 {changed} 行")

    for area_id, abbr, old, new, why in NAME_FIXES:
        path = BY_PROV / f"{abbr}-area.csv"
        cols, rows = _read(path)
        hit = [r for r in rows if r.get("area_id") == area_id and r.get("name") == old]
        if not hit:
            stale = [r.get("name") for r in rows if r.get("area_id") == area_id]
            print(f"  跳过 {area_id} name: 无「{old}」（现值 {stale}）")
            continue
        for r in hit:
            r["name"] = new
            if "name_norm" in r:
                r["name_norm"] = new
        changed += len(hit)
        print(f"  {area_id} name: {old} -> {new}  ({why})")
        if not dry:
            _write(path, cols, rows)

    print(f"{'dry-run，' if dry else ''}共改 {changed} 行")

    # 整行重建：只处理 created_by=repair-2026-09 且字段仍是垃圾值的行
    garbage = {"repair-2026-09", "2023-01-01", "2026-09-30T12:00:00+08:00", ""}

    def _corrupt(r: dict[str, str]) -> bool:
        tc = (r.get("town_codes") or "").strip()
        cd = (r.get("cover_desc") or "").strip()
        sm = (r.get("summary") or "").strip()
        # town_codes 是数字（错位吞进来的村数）或垃圾值，且描述/摘要也是垃圾
        return (tc.isdigit() or tc in garbage) and (cd in garbage or sm in garbage)

    by_abbr: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    rebuilt = 0
    for area_id, (abbr, fields, why) in ROW_REBUILDS.items():
        path = BY_PROV / f"{abbr}-area.csv"
        if abbr not in by_abbr:
            by_abbr[abbr] = _read(path)
        cols, rows = by_abbr[abbr]
        hit = [
            r for r in rows
            if r.get("area_id") == area_id
            and r.get("created_by") == "repair-2026-09"
            and _corrupt(r)
        ]
        if not hit:
            print(f"  跳过 {area_id} 重建：不是 repair-2026-09 留下的坏行（已是修好状态）")
            continue
        for r in hit:
            r.update(fields)
            r.update(ROW_REBUILD_CLEAR)
            if r.get("created_at") in garbage:
                r["created_at"] = BATCH_TIMESTAMP
            r["updated_at"] = BATCH_TIMESTAMP
        rebuilt += len(hit)
        print(f"  {area_id} 整行重建 {len(fields)} 字段 + 清占位日期  ({why})")
    if not dry and rebuilt:
        for abbr, (cols, rows) in by_abbr.items():
            _write(BY_PROV / f"{abbr}-area.csv", cols, rows)
    changed += rebuilt

    # city_code 修正（只动 area.csv，county 不变）
    for area_id, abbr, old, new, why in CITY_FIXES:
        path = BY_PROV / f"{abbr}-area.csv"
        cols, rows = _read(path)
        hit = [r for r in rows if r.get("area_id") == area_id and r.get("city_code") == old]
        if not hit:
            stale = [r.get("city_code") for r in rows if r.get("area_id") == area_id]
            print(f"  跳过 {area_id} city: 无 {old}（现值 {stale}）")
            continue
        for r in hit:
            r["city_code"] = new
        changed += len(hit)
        print(f"  {area_id} city_code: {old} -> {new}  ({why})")
        if not dry:
            _write(path, cols, rows)

    # 清空被污染的数值字段（值仍在 cover_desc/原文里，不丢证据）
    for area_id, abbr, field, old, why in FIELD_CLEARS:
        path = BY_PROV / f"{abbr}-area.csv"
        cols, rows = _read(path)
        hit = [r for r in rows if r.get("area_id") == area_id and (r.get(field) or "").strip() == old]
        if not hit:
            stale = [r.get(field) for r in rows if r.get("area_id") == area_id]
            print(f"  跳过 {area_id} {field}: 无 {old!r}（现值 {stale}）")
            continue
        for r in hit:
            r[field] = ""
        changed += len(hit)
        print(f"  {area_id} {field}: 清空 {old!r}  ({why})")
        if not dry:
            _write(path, cols, rows)

    print(f"{'dry-run，' if dry else ''}累计共改 {changed} 行")
    if not dry and changed:
        print("接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
