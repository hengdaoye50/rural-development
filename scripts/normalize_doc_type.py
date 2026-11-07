"""按标题把 doc_type='其他' 的记录归入更精确的文种。

只处理枚举扩展前入库的存量；不改变任何文件内容，只改 doc_type 一列。
判定基于标题的字面文种词，属事实性分类，不做内容推断。

用法：
  python scripts/normalize_doc_type.py --dry-run     # 只看会改什么
  python scripts/normalize_doc_type.py               # 落盘
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BY_PROV = ROOT / "data" / "clean" / "by_province"

# 顺序敏感：先匹配更具体的
RULES: list[tuple[str, str]] = [
    (r"(建议|提案|议案).{0,10}(答复|复函|回复)|答复的函|复函|办理结果", "答复"),
    (r"工作总结|工作回顾|工作要点|工作计划|年度总结|半年度", "总结"),
    (r"政府工作报告|工作报告", "报告"),
    (r"入库指南|申报指南|操作指南|编制指南", "指南"),
    (r"新闻发布会|发布会|新闻发布", "新闻发布"),
    (r"实施意见|指导意见|若干意见", "意见"),
    (r"实施方案|行动方案|工作方案|方案", "方案"),
    (r"规划|纲要", "规划"),
    (r"办法|细则|规定", "办法"),
    (r"通知", "通知"),
    (r"批复", "批复"),
    (r"公示|公告|公示稿|征求意见", "公告"),
    (r"名单|名录", "名单"),
    (r"简报|动态|进展|推进|召开|举办", "动态"),
]


def _read(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), [r for r in rd if any(r.values())]


def _write(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") or "" for h in header})


def classify(title: str) -> str:
    for pat, target in RULES:
        if re.search(pat, title or ""):
            return target
    return ""


def main() -> int:
    dry = "--dry-run" in sys.argv
    changed_total = 0
    dist: Counter = Counter()
    samples: list[tuple[str, str, str]] = []

    for p in sorted(BY_PROV.glob("*-policy.csv")):
        header, rows = _read(p)
        if not header:
            continue
        touched = 0
        for r in rows:
            if (r.get("doc_type") or "") != "其他":
                continue
            new = classify(r.get("title") or "")
            if not new or new == "其他":
                continue
            if dry:
                samples.append((r.get("policy_id", ""), r.get("title", "")[:44], new))
            r["doc_type"] = new
            dist[new] += 1
            touched += 1
        if touched:
            changed_total += touched
            if not dry:
                _write(p, header, rows)
            print(f"  {p.name}: {touched} 条")

    print(f"\n{'[dry-run] ' if dry else ''}共 {changed_total} 条 doc_type 从「其他」改为：")
    for k, v in dist.most_common():
        print(f"  {k:6s} {v:4d}")

    if dry and samples:
        print("\n样例：")
        for pid, title, new in samples[:20]:
            print(f"  {pid:10s} → {new:6s}  {title}")

    if dry:
        print("\n未落盘。去掉 --dry-run 执行。")
    else:
        print("\n接着跑：merge_by_province -> build_db -> validate_db")
    return 0


if __name__ == "__main__":
    sys.exit(main())
