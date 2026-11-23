# -*- coding: utf-8 -*-
"""解析吉林 v2 分县核查表 → 候选 CSV（按等级决定状态）。"""
from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(".")
SRC = Path(r"D:\HuaweiMoveData\Users\zjh22\Desktop\吉林片区化_分县核查_v2_20261123.md")
RAW = ROOT / "data/raw/JL/20261123-jilin-v2/原文.md"
OUT = ROOT / "data/stage/candidates/area-media-roster-JL-v2.csv"

BAD_NAME = ("未具名", "未找到", "未公开", "未命名", "无正式片区名")
SKIP_GRADE = ("X",)  # X=无证据；D 多为间接
CITY_CODE = {"长春市": "220100", "吉林市": "220200", "四平市": "220300", "辽源市": "220400",
             "通化市": "220500", "白山市": "220600", "松原市": "220700", "白城市": "220800",
             "延边朝鲜族自治州": "222400"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    text = SRC.read_text(encoding="utf-8")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, RAW)

    region: dict[str, str] = {}
    dup: set[str] = set()
    for line in (ROOT / "data/clean/region.csv").read_text(encoding="utf-8-sig").splitlines()[1:]:
        p = line.split(",")
        if len(p) >= 4 and p[3] == "county" and p[0].startswith("22"):
            if p[1] in region:
                dup.add(p[1])
            region[p[1]] = p[0]
    for d in dup:
        region.pop(d, None)

    rows = []
    city = ""
    for line in text.splitlines():
        m = re.match(r"^###\s*\d+\.\s*(.+?)（\d+）", line)
        if m:
            city = m.group(1).strip()
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        county, name, villages, typ, source, link, quote, grade = cells[:8]
        if county in ("市县区",) or set(county) <= {"-"}:
            continue
        if any(b in name for b in BAD_NAME) or name in ("", "—"):
            continue
        g = grade[0].upper()
        if g in SKIP_GRADE or not g.isalpha():
            continue
        code = region.get(county)
        if not code:
            print(f"!! 县码未匹配：{county} / {name}")
            continue
        nm = re.sub(r"[（(].*?[）)]", "", name).strip().strip("“”\"'")
        if not nm or len(nm) < 3:
            continue
        rows.append({
            "name": nm, "type_code": "T01",
            "city_code": CITY_CODE.get(city) or (code[:4] + "00"),
            "county_code": code, "cover_desc": f"{county}·{villages or '—'}；{typ or '—'}（{g} 级证据）",
            "status": "运行中" if g in ("A", "B") else "待核",
            "founded_ymd": "2026" if g == "A" else "", "founded_precision": "year" if g == "A" else "unknown",
            "issuer": "吉林省农业农村厅" if g == "A" else f"{county}政府/部门",
            "summary": "", "source_url": link if link.startswith("http") else "",
            "source_title": source[:80], "publisher": source.split("《")[0].strip("《》 ")[:40] or "吉林省",
            "published_ymd": "", "credibility": "A" if g == "A" else ("B" if g == "B" else "C"),
            "excerpt": quote.strip("“”\"'")[:200] or nm,
            "local_path": "data/raw/JL/20261123-jilin-v2/原文.md", "grade": g,
        })
    # 拆多名 + 清噪声（只留真正的片区名）
    DROP = ("工程", "项目", "试点县", "组团", "党委", "联席", "线索", "中心村", "示范工程")
    DROP_SRC = ("国土空间", "规划公示", "规划纲要")
    expanded = []
    for r in rows:
        if any(k in (r["source_title"] + r["cover_desc"]) for k in DROP_SRC):
            continue  # 国土空间规划的「片区」是规划分区，不是乡村振兴片区
        for part in re.split(r"[、／/]", r["name"]):
            nm = re.sub(r"[“”\"'‘’]", "", part).strip()
            if "片区" not in nm or len(nm) < 4:
                continue
            if any(d in nm for d in DROP) and "示范片区" not in nm:
                continue
            if nm.endswith("村片区") or nm.endswith("农场片区"):
                continue  # 村级单元，非片区
            if nm in ("青山镇片区", "安石镇朝阳村一托五片区", "叶赫片区"):
                continue  # 与已有记录或同名长名重复
            rr = dict(r)
            rr["name"] = nm
            expanded.append(rr)
    rows = expanded

    # 去重（县+名）
    seen, uniq = set(), []
    for r in rows:
        k = (r["county_code"], re.sub(r"[\s（）()·—\-]+", "", r["name"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    cols = ["name", "type_code", "city_code", "county_code", "cover_desc", "status", "founded_ymd",
            "founded_precision", "issuer", "summary", "source_url", "source_title", "publisher",
            "published_ymd", "credibility", "excerpt", "local_path", "grade"]
    tmp = OUT.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        w.writerows(uniq)
    tmp.replace(OUT)
    from collections import Counter
    c = Counter(r["grade"] for r in uniq)
    print(f"{len(uniq)} 条 -> {OUT.relative_to(ROOT)}｜等级 {dict(c)}")
    for r in uniq[:40]:
        print(f"  [{r['grade']}] {r['name']}｜{r['county_code']}｜{r['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
