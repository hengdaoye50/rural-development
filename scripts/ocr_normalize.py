"""OCR 结果的确定性纠错层。

OCR 有两类系统性错误换引擎也治不好，只能靠规则兜：

1. **文号括号**：扫描件里「〔2024〕」与「（2024）」字形几乎一致，模型普遍认成全角括号。
   公文文号是强模式，用正则归一即可。
2. **专名形近字**：如「五好两宜」→「五好两宣」。用库里的片区名、市县名建词表，
   只在「与某个已知术语只差一个形近字」时替换，避免乱改。

两条规则都只做**可逆、可审计**的替换，并把每处改动打印出来供人工复核。

用法：
    python scripts/ocr_normalize.py --check 原文.md      # 只报告会改什么
    python scripts/ocr_normalize.py --apply 原文.md      # 就地改写
    python scripts/ocr_normalize.py --check --quiet 原文.md
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

# 公文文号：机关简称（含括号/书名号等）+ 年份 + 序号 + 号
DOC_NO_RE = re.compile(
    r"([\u4e00-\u9fa5A-Za-z]{2,20})[（(\[【](\d{4})[）)\]】](\s*第?\s*\d+\s*号)"
)

# 中文 OCR 常见形近字对（双向）。只用于「已知术语 ±1 字」的定向纠错，不做全局替换。
CONFUSABLE = [
    ("宜", "宣"), ("已", "己"), ("已", "巳"), ("未", "末"), ("汨", "汩"),
    ("州", "洲"), ("径", "泾"), ("城", "诚"), ("镇", "慎"), ("园", "圆"),
    ("治", "冶"), ("历", "厉"), ("侯", "候"), ("析", "折"), ("拔", "拨"),
    ("晴", "睛"), ("候", "侯"), ("徒", "徙"), ("析", "淅"), ("藉", "籍"),
    ("瀛", "赢"), ("鳌", "鳌"), ("墩", "敦"), ("坝", "垻"), ("塘", "搪"),
]

# 名称里常见但无区分度的尾缀，切掉后作为术语主体
SUFFIXES = [
    "乡村振兴示范片区", "宜居宜业和美乡村片区", "和美乡村示范片区", "和美乡村片区",
    "乡村振兴片区", "示范片区", "重点片区", "片区组团", "片区", "示范区", "示范带",
]


def load_terms() -> set[str]:
    """从库里取片区名与市县名，切成术语主体。"""
    if not DB.exists():
        return set()
    con = sqlite3.connect(DB)
    terms: set[str] = set()
    try:
        for (name,) in con.execute("select name from area where name is not null"):
            t = name.strip()
            for suf in SUFFIXES:
                if t.endswith(suf) and len(t) - len(suf) >= 2:
                    t = t[: -len(suf)]
                    break
            t = t.strip("\"'“”「」· ")
            if len(t) >= 3:
                terms.add(t)
        for (name,) in con.execute("select name from region where level='county'"):
            n = (name or "").strip()
            if len(n) >= 3:
                terms.add(n)
                terms.add(n.rstrip("市县区"))
    finally:
        con.close()
    return {t for t in terms if len(t) >= 3}


def variants(term: str) -> set[str]:
    """生成与 term 只差一个形近字的变体。"""
    out: set[str] = set()
    for i, ch in enumerate(term):
        for a, b in CONFUSABLE:
            if ch == a:
                out.add(term[:i] + b + term[i + 1:])
            elif ch == b:
                out.add(term[:i] + a + term[i + 1:])
    return out


def build_variant_map(terms: set[str]) -> dict[str, str]:
    """变体 -> 正确术语。只收「变体本身不是已知术语」的，避免互相打架。"""
    m: dict[str, str] = {}
    for t in terms:
        for v in variants(t):
            if v in terms:
                continue
            m.setdefault(v, t)
    return m


def normalize(text: str, terms: set[str]) -> tuple[str, list[tuple[str, str, str]]]:
    """返回 (新文本, 改动列表 [(类型, 原, 新)])。"""
    changes: list[tuple[str, str, str]] = []

    def _doc_no(m: re.Match[str]) -> str:
        whole = m.group(0)
        fixed = f"{m.group(1)}〔{m.group(2)}〕{m.group(3)}"
        if fixed != whole:
            changes.append(("文号括号", whole, fixed))
        return fixed

    text = DOC_NO_RE.sub(_doc_no, text)

    vmap = build_variant_map(terms)
    if vmap:
        # 长变体优先，避免短变体先命中把长词切碎
        for v in sorted(vmap, key=len, reverse=True):
            fixed = vmap[v]
            if v not in text:
                continue
            n = text.count(v)
            text = text.replace(v, fixed)
            changes.append(("专名形近字", f"{v}×{n}", fixed))

    return text, changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--check", action="store_true", help="只报告，不写回")
    ap.add_argument("--apply", action="store_true", help="就地改写")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not (args.check or args.apply):
        print("请给 --check 或 --apply", file=sys.stderr)
        return 2

    p = Path(args.path)
    raw = p.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    terms = load_terms()
    new, changes = normalize(text, terms)

    if not args.quiet:
        print(f"术语表 {len(terms)} 条；命中改动 {len(changes)} 处")
        for kind, old, newv in changes:
            print(f"  [{kind}] {old}  ->  {newv}")

    if args.apply and new != text:
        enc = raw.decode("utf-8-sig")
        out = ("\ufeff" if has_bom else "") + new
        p.write_text(out, encoding="utf-8", newline="\n")
        print(f"已写回 {p}（BOM={'保留' if has_bom else '无'}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
