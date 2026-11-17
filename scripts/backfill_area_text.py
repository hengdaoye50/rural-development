"""回填空缺的 `summary` / `cover_desc`，并清理 summary 的日期前缀。

原则：**只摘录、不撰写。** 从该片区所挂政策的原文里摘一句含片区名的逐字句，
长度 30–200 字、终止于句末标点。摘不到就留空——留空比编造一句强。

同时处理一类既有缺陷：早期批次把日期写进了 summary（`2023-01-01｜【证据待核】…`），
日期部分与 `founded_ymd` 重复，剥掉即可，标记内容保留。

每一处改动都记进 `reports/qa/text-backfill-log.csv`：area_id / 字段 / 来源 policy / 写入文本。

    python scripts/backfill_area_text.py --dry-run
    python scripts/backfill_area_text.py
    # 接着跑 merge_by_province -> build_db -> validate_db
"""
from __future__ import annotations

import csv
import os
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"
BY_PROV = ROOT / "data" / "clean" / "by_province"
LOG = ROOT / "reports" / "qa" / "text-backfill-log.csv"

MIN_LEN, MAX_LEN = 30, 200
# 摘要开头常见「1.」「3、「（一）」等列表序号，摘录时剥掉
LIST_HEAD = re.compile(r'^\s*(?:[（(]?[0-9一二三四五六七八九十]{1,3}[）)、\.．]\s*|[（(][一二三四五六七八九十]{1,3}[）)]\s*)')
DATE_HEAD = re.compile(
    r'^\s*\d{4}(?:-\d{2}(?:-\d{2})?)?(?:T[\d:+]+)?\s*[｜|]\s*')


def core_name(name: str) -> str:
    return re.sub(r'(片区组团|示范廊带|示范带|示范片|组团片区|田园综合体|片区)$', '', name or "")


def sentences(text: str):
    for seg in re.split(r'(?<=[。；！？\n])', text):
        s = " ".join(seg.split())
        s = LIST_HEAD.sub("", s).strip()
        if MIN_LEN <= len(s) <= MAX_LEN:
            yield s


def _plausible(s: str) -> bool:
    """过滤表格行、标题行、目录行——它们不是句子，塞进 summary 只会更脏。"""
    if s.count("|") >= 2 or s.startswith("#") or s.startswith(">"):
        return False
    if any(w in s for w in ("文章来源", "点击进入", "上一篇", "下一篇", "打印本页")):
        return False
    cn = len(re.findall(r"[\u4e00-\u9fa5]", s))
    if cn < 16:                      # 中文占比过低，多半是表格/编号行
        return False
    if cn / max(len(s), 1) < 0.45:
        return False
    return True


def pick(text: str, keys: list[str]) -> str:
    for s in sentences(text):
        if any(k and k in s for k in keys) and _plausible(s):
            return s
    return ""


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    if not DB.exists():
        print(f"找不到 {DB}")
        return 1
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    pol = {r["policy_id"]: r for r in con.execute(
        "select policy_id, title, local_path from policy")}
    links: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in con.execute("select area_id, policy_id, rel from area_policy_map"):
        links[r["area_id"]].append((r["policy_id"], r["rel"]))

    cache: dict[str, str] = {}

    def body(pid: str) -> str:
        if pid not in cache:
            t = ""
            p = pol.get(pid)
            if p and p["local_path"]:
                f = ROOT / p["local_path"]
                if f.exists():
                    t = f.read_text(encoding="utf-8", errors="ignore")
            cache[pid] = t
        return cache[pid]

    areas = list(con.execute("""select area_id, name, cover_desc, summary from area
                                where record_state='active'"""))
    plan: list[tuple[str, str, str, str]] = []   # area_id, field, policy_id, text
    date_prefix_fixed = 0

    for a in areas:
        aid = a["area_id"]
        keys = [a["name"], core_name(a["name"])]
        # 优先 primary/support，其次 mention
        order = ([p for p, r in links.get(aid, []) if r in ("primary", "support")]
                 + [p for p, r in links.get(aid, []) if r == "mention"])

        # 1) summary 以日期开头：剥离日期前缀（内容保留）
        sm = (a["summary"] or "").strip()
        if DATE_HEAD.match(sm):
            stripped = DATE_HEAD.sub("", sm).strip()
            if stripped and stripped != sm:
                plan.append((aid, "summary", "", stripped))
                date_prefix_fixed += 1
        # 2) summary 为空：摘一句
        elif not sm:
            for pid in order:
                got = pick(body(pid), keys)
                if got:
                    plan.append((aid, "summary", pid, got))
                    break
        # 3) cover_desc 与 name 相同：换成含范围描述的句子
        #    必须同时有「范围动词」与「地名/规模」，否则会摘到品牌宣传句
        if (a["cover_desc"] or "").strip().rstrip("。") == (a["name"] or "").strip():
            for pid in order:
                got = pick(body(pid), keys + ["涉及", "覆盖", "包括", "范围"])
                # 必须有「数字+范围单位」，否则「社区居家养老服务实现全覆盖」这类也会被摘进来
                if got and re.search(r'\d+\s*(个\s*(村|镇|乡|街道|社区)|平方公里|公里)', got) \
                        and re.search(r"(涉及|覆盖|包括|范围|辖)", got):
                    plan.append((aid, "cover_desc", pid, got))
                    break

    by_field = defaultdict(int)
    for _, f, _, _ in plan:
        by_field[f] += 1
    print(f"计划改动 {len(plan)} 处：" + "，".join(f"{k} {v}" for k, v in by_field.items())
          + f"（其中 summary 剥日期前缀 {date_prefix_fixed} 处）")

    if not dry and plan:
        # 按省写入 by_province/{ABBR}-area.csv
        by_abbr: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
        for path in sorted(BY_PROV.glob("*-area.csv")):
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                rd = csv.DictReader(f)
                by_abbr[path.name.split("-")[0]] = (list(rd.fieldnames or []), [r for r in rd if any(r.values())])
        touched = set()
        for aid, field, pid, text in plan:
            for abbr, (cols, rows) in by_abbr.items():
                hit = [r for r in rows if r.get("area_id") == aid]
                if hit:
                    hit[0][field] = text
                    touched.add(abbr)
                    break
            else:
                print(f"  !! {aid} 不在 by_province 任何 area CSV")
        for abbr in touched:
            cols, rows = by_abbr[abbr]
            path = BY_PROV / f"{abbr}-area.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                for r in rows:
                    w.writerow({c: r.get(c, "") for c in cols})
        LOG.parent.mkdir(parents=True, exist_ok=True)
        old = []
        if LOG.exists():
            with LOG.open("r", encoding="utf-8-sig", newline="") as f:
                old = [r for r in csv.DictReader(f) if r.get("area_id")]
        merged = {(r["area_id"], r["field"]): r for r in old}
        for aid, field, pid, text in plan:
            merged[(aid, field)] = {"area_id": aid, "field": field,
                                    "source_policy_id": pid, "written_text": text}
        with LOG.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["area_id", "field", "source_policy_id", "written_text"])
            w.writeheader()
            w.writerows(merged.values())
        print(f"已写 {len(touched)} 个 by_province 文件；改动明细 -> {LOG.relative_to(ROOT)}")
        print("接着跑：merge_by_province -> build_db -> validate_db")
    elif dry:
        for p in plan[:8]:
            print(f"   {p[0]} {p[1]:10s} <- {p[2]:8s} {p[3][:60]}")
        print("dry-run，未写盘")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
