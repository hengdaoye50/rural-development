"""名单类政策的全文完整性审计（多信号交叉，只排序不判定）。

背景：政策层硬约束是「必须存全文」，但 validate_db 只校验 full_text_chars 与哈希一致
——那只证明「存的和我算的一致」，不证明「存的就是原文全部」。采集端去导航、切容器、
OCR 任一步都可能截断，而截断后的文本依然自洽、依然能通过全部校验。

首个反例：广西 P450007 的 full_text 只列 8 个田园综合体，实际该批 16 个。

本脚本不算「是否截断」，只按可疑度排序，供人工核原文。四个信号：

  S1 声明数 vs 编号条目数      原文写 N 个，正文只数列出 M 条
  S2 声明数 vs 关键名词出现次数  从标题推断计量词（田园综合体/片区/示范带…）
  S3 正文结尾形态              正常应以落款/日期/附件说明收尾；
                               以顿号、逗号、「等」、编号片段收尾说明断了
  S4 字符量与声明数不匹配        每条平均不足 ~40 汉字，不合常理

用法：
  python scripts/audit_roster_completeness.py
  python scripts/audit_roster_completeness.py --csv reports/qa/roster-completeness.csv
  python scripts/audit_roster_completeness.py --top 20
"""
from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# 计量词：出现在标题里，说明这份文件在「逐个列某类单元」
COUNTER_WORDS = [
    "田园综合体", "示范片区", "片区组团", "样板片区", "重点片区", "精品片区",
    "示范带", "样板带", "先导区", "示范片", "组团片区", "片区",
]

# 编号条目：1. / 1、 / （1） / (1) / 第1个
NUM_ITEM = re.compile(r"(?m)^\s*(?:[（(]\s*\d{1,3}\s*[)）]|\d{1,3}\s*[.、．])\s*\S")

# 正常结尾应包含这些收尾标志之一
TAIL_OK = re.compile(
    r"(年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\d{4}-\d{2}-\d{2}|附件|印发|代章|"
    r"公开方式|来源[:：]|发布[:：]|特此通知|特此公告|特此批复|此复|"
    r"以上报告|请予审议|予以公布|现予公布|抄送|主题词)"
)

# 断尾迹象：正文真正以标点/序号结尾（字符类必须出现，不能可选）
TAIL_BAD = re.compile(r"(?:[、，,；;：:（(【\[]|[等等]|\d{1,3}\s*[.、．])\s*$")


def count_items(text: str) -> int:
    """数编号条目：1. / 1、 / （1） / (1)。"""
    return len(NUM_ITEM.findall(text))


INLINE = re.compile(r"(\d{1,3})\s*个[^：:\n]{0,12}[：:]\s*([^。\n]{4,400})")


def count_inline(text: str, word: str) -> int:
    """数「N个<计量词>：A、B、C…」这种内联枚举的实际名字个数。

    浙江各县发展轴规划普遍用这种写法（「10个乡村片区组团：仙果丁宅、白马春晖、…」），
    只数编号条目会把完整文本误判成截断。
    """
    best = 0
    for m in INLINE.finditer(text):
        declared, body = int(m.group(1)), m.group(2)
        # 名字之间用顿号/逗号分隔
        parts = [p.strip() for p in re.split(r"[、，,；;]", body) if p.strip()]
        if parts:
            best = max(best, min(len(parts), declared))
    return best


def counter_hits(title: str, text: str) -> tuple[str, int, int]:
    """返回 (计量词, 标题命中数, 正文出现次数)。取标题里出现次数最多的计量词。"""
    best, best_n = "", 0
    for w in COUNTER_WORDS:
        n = title.count(w)
        if n > best_n:
            best, best_n = w, n
    if not best:
        return "", 0, 0
    return best, best_n, text.count(best)


def main() -> int:
    top = 30
    out_csv = ""
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    if "--csv" in sys.argv:
        out_csv = sys.argv[sys.argv.index("--csv") + 1]

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT policy_id, title, province_code, local_path, full_text_chars,
               target_areas, doc_type, source_kind
        FROM policy
        WHERE target_areas IS NOT NULL AND target_areas != ''
          -- 只审「逐个列举」类文件。新闻稿/部门动态里的 target_areas 记的是
          -- 「涉及多少个片区」（原文明确写出），本来就不该把条目全列出来，
          -- 拿它当枚举数比对必然全是假阳性。
          AND source_kind NOT IN ('新闻发布', '部门动态')
          AND (doc_type IN ('名单', '批复', '通知', '公告')
               OR title LIKE '%名单%' OR title LIKE '%公布%' OR title LIKE '%批复%')
        ORDER BY policy_id
        """
    ).fetchall()

    recs = []
    for r in rows:
        body = ROOT / r["local_path"]
        if not body.exists():
            continue
        text = body.read_text(encoding="utf-8")
        try:
            declared = int(float(r["target_areas"]))
        except (TypeError, ValueError):
            continue
        chars = r["full_text_chars"] or 0
        n_items = count_items(text)
        word, _t_hits, w_count = counter_hits(r["title"], text)
        n_inline = count_inline(text, word)
        enumerated = max(n_items, n_inline)
        tail = text.rstrip()[-40:]

        signals = []
        # S1：声明数显著多于「编号条目」或「内联顿号枚举」中较多的那个
        if declared >= 5 and enumerated >= 2 and enumerated < declared * 0.7:
            signals.append(f"S1 声明{declared} vs 枚举{enumerated}(编号{n_items}/内联{n_inline})")
        # S2：关键名词出现次数明显少于声明数（说明后文没列到）
        if declared >= 5 and word and 0 < w_count < declared:
            signals.append(f"S2 {word}仅出现{w_count}次<声明{declared}")
        # S3：结尾不像收尾
        if not TAIL_OK.search(tail) and TAIL_BAD.search(text.rstrip()):
            signals.append("S3 结尾疑似中断")
        # S4：每条平均字符量过低
        if declared >= 5 and chars / declared < 40:
            signals.append(f"S4 每条均{chars/declared:.0f}字")

        if signals:
            recs.append({
                "policy_id": r["policy_id"],
                "province_code": r["province_code"],
                "declared": declared,
                "num_items": enumerated,
                "counter_word": word,
                "counter_count": w_count,
                "full_text_chars": chars,
                "n_signals": len(signals),
                "signals": " | ".join(signals),
                "title": r["title"][:56],
                "tail": tail.replace("\n", " "),
            })

    recs.sort(key=lambda x: (-x["n_signals"], x["declared"] - x["num_items"], -x["declared"]))

    print(f"名单类政策（含 target_areas）{len(rows)} 条，命中可疑信号 {len(recs)} 条\n")
    print(f"{'policy':<9}{'省':<4}{'声明':>4}{'编号':>4}{'词次':>5}{'字数':>7}{'信号':>4}  标题")
    for r in recs[:top]:
        print(f"{r['policy_id']:<9}{r['province_code'][:2]:<4}{r['declared']:>4}"
              f"{r['num_items']:>4}{r['counter_count']:>5}{r['full_text_chars']:>7}"
              f"{r['n_signals']:>4}  {r['title']}")
        print(f"          {r['signals']}")
        print(f"          尾：…{r['tail'][-34:]}")

    if out_csv:
        p = ROOT / out_csv
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(recs[0].keys()) if recs else ["policy_id"])
            w.writeheader()
            w.writerows(recs)
        print(f"\n全量 {len(recs)} 条 -> {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
