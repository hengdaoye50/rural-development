"""审计 area_policy_map 的链接真实性：政策全文到底有没有点名这个片区。

背景：`audit_missing_policy_links.py` 查反面（正文点名了但没挂链接）。
本脚本查正面——**挂上的链接是否名副其实**。挂错或挂空的链接会让
「有政策依据的片区占比」虚高，所以覆盖率先要经得起这一关。

判据演进说明（重要，避免重复踩坑）：
  1. 早期用「按顺序命中 60% 的字」做中间档，实测量出 39% 落在该档——
     那是噪声：十万字长文里任意 3~4 字短名几乎必然「按顺序命中」。
     该档已删除，只保留**连续子串命中**这类硬判据。
  2. 片区名常带完整行政路径（「嘉兴市南湖区大三星片区」），只剥通名会漏判。
     故对每个名字生成多个候选串（全名 / 去通名 / 逐层剥行政区划前缀 /
     逐字剥前导字的后缀 / 破折号分段），任一候选连续命中即算点名。

分档（对每条 primary/support 链接，取最优）：
    exact     全名（去引号）连续命中
    core      去掉「片区/组团/示范带」等通名后连续命中
    stripped  再剥掉行政前缀后连续命中
    tail      核心名再逐字剥前导字后，某个后缀连续命中
    segments  名字里「—」「·」分段，多数段各自命中（复合型村名带）
    place_only 正文未点名片区品牌名，只有该片区的县名/镇名出现——弱依据
    missing   以上全不命中——链接很可能挂错
    no_text   local_path 缺失或读不到

用法：
    python scripts/audit_link_veracity.py
    python scripts/audit_link_veracity.py --csv reports/qa/link-veracity.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "db" / "片区库.sqlite3"

QUOTES = "\"'“”‘’「」『』《》 "
GENERIC = [
    "乡村振兴示范片区", "乡村振兴片区", "和美乡村片区", "示范片区", "组团片区",
    "共富片区", "精品片区", "乡村振兴示范带", "示范带", "示范片", "片区",
    "组团", "联合体", "集聚区", "党建联合体",
]
ADMIN_RE = re.compile(r"^[\u4e00-\u9fa5]{1,6}?(省|自治区|市|区|县|自治县|旗|镇|乡|街道|村)")
SPLIT_RE = re.compile(r"[—－\-–~至到]")

TIER_RANK = {
    "exact": 6, "core": 5, "stripped": 4, "tail": 3, "segments": 2,
    "place_only": 1, "missing": 0, "no_text": -1,
}
TIER_ORDER = ["exact", "core", "stripped", "tail", "segments", "place_only", "missing", "no_text"]


PAREN_RE = re.compile(r"[（(]([^）)]*)[）)]")


def split_paren(s: str) -> tuple[str, list[str]]:
    """拆出「主体名」与括号里的补充信息。

    库内不少片区名带括号注释：「上坝片区（金沙木孔）」「两湖片区（省级宜居宜业…）」。
    括号里通常是「县名+镇名」这类地理锚点，是判弱依据的关键；
    而括号本身会污染候选串，故主体名单独参与匹配。
    """
    inner = [m.group(1) for m in PAREN_RE.finditer(s)]
    return PAREN_RE.sub("", s).strip(), [x for x in inner if x.strip()]


def clean_name(s: str) -> str:
    s, _ = split_paren(s)
    for ch in QUOTES:
        s = s.replace(ch, "")
    return s.strip()


def strip_generic(s: str) -> str:
    for suf in GENERIC:
        if s.endswith(suf) and len(s) > len(suf) + 1:
            return s[: -len(suf)]
    return s


def strip_admin(s: str) -> str:
    while True:
        m = ADMIN_RE.match(s)
        if not m or len(s) - m.end() < 2:
            return s
        s = s[m.end():]


def candidates(name: str) -> list[tuple[str, str]]:
    """返回 [(档位, 候选串)]，按档位从强到弱。

    除全名/去通名/剥行政前缀外，还逐字剥掉核心名的前导字生成后缀候选：
    政策文件常省略行政前缀（「开州雪宝山片区」在正文里只写「雪宝山片区」），
    不给后缀候选就会把这些**真依据**判成无关。
    """
    full = clean_name(name)
    core = strip_generic(full)
    stripped = strip_admin(core)
    out: list[tuple[str, str]] = [("exact", full)]
    if core and core != full:
        out.append(("core", core))
    if stripped and stripped not in (full, core):
        out.append(("stripped", stripped))
    base = stripped or core
    # 只对短核心名做逐字剥离：长名（复合村名带）剥出来的 3 字残片
    # 在万字长文里几乎必然命中，会把「无关」误判成「点名」。
    if len(base) <= 6:
        min_len = 2 if len(base) <= 4 else 3
        for i in range(1, len(base) - min_len + 1):
            out.append(("tail", base[i:]))
    return [(t, s) for t, s in out if len(s) >= 2]


def text_of(p: str | None, cache: dict[str, str]) -> str:
    if not p:
        return ""
    if p in cache:
        return cache[p]
    f = ROOT / p
    t = ""
    if f.exists():
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            t = ""
    cache[p] = t
    return t


def place_tokens(county_name: str, town_codes: str) -> list[str]:
    """该片区的县名与镇名，用来判「弱依据」还是「挂错」。

    县名去掉「县/区/市」后缀再搜（「庆云县」-> 「庆云」），镇名同时保留
    带后缀与去后缀两种写法（「崔口镇」-> 「崔口」）。
    """
    toks: list[str] = []
    cn = (county_name or "").strip()
    if len(cn) >= 3:
        toks.append(re.sub(r"(县|区|市|自治县|旗)$", "", cn))
    for t in re.split(r"[/、,，]", town_codes or ""):
        t = t.strip()
        if not t:
            continue
        toks.append(t)
        base = re.sub(r"(镇|乡|街道|苏木)$", "", t)
        if len(base) >= 2:
            toks.append(base)
    return [t for t in dict.fromkeys(toks) if len(t) >= 2]


def paren_place_tokens(area_name: str) -> list[str]:
    """括号里的「金沙木孔」这类锚点，拆成 2 字以上可搜索片断。"""
    _, inner = split_paren(area_name)
    toks: list[str] = []
    for x in inner:
        x = re.sub(r"(县|区|市|镇|乡|街道|村|组)", "", x)
        if 2 <= len(x) <= 8:
            toks.append(x)
            # 「金沙木孔」可能由两个地名连写，补上前两字/后两字
            if len(x) >= 4:
                toks.extend([x[:2], x[-2:]])
    return [t for t in dict.fromkeys(toks) if len(t) >= 2]


def classify(area_name: str, compact: str) -> str:
    if not compact:
        return "no_text"
    for tier, cand in candidates(area_name):
        if cand in compact:
            return tier
    raw = clean_name(area_name)
    parts = [strip_admin(strip_generic(p)) for p in SPLIT_RE.split(raw)]
    parts = [p for p in parts if len(p) >= 2]
    if len(parts) >= 2:
        hit = sum(1 for p in parts if p in compact)
        if hit >= max(2, (len(parts) + 1) // 2):
            return "segments"
    return "missing"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT m.area_id, m.policy_id, m.rel, a.name AS area_name, a.province_code,
               a.status, a.town_codes, r.name AS county_name,
               p.title, p.local_path
        FROM area_policy_map m
        JOIN area a ON a.area_id = m.area_id
        LEFT JOIN region r ON r.region_code = a.county_code
        JOIN policy p ON p.policy_id = m.policy_id
        WHERE m.rel IN ('primary','support') AND a.record_state='active'
    """).fetchall()
    print(f"primary/support 链接 {len(rows)} 条")

    cache: dict[str, str] = {}
    out = []
    stat = Counter()
    area_tier: dict[str, str] = {}
    meta: dict[str, tuple[str, str]] = {}

    for r in rows:
        compact = re.sub(r"\s+", "", text_of(r["local_path"], cache))
        tier = classify(r["area_name"], compact)
        if tier == "missing":
            toks = place_tokens(r["county_name"], r["town_codes"]) + paren_place_tokens(r["area_name"])
            if any(t in compact for t in toks):
                tier = "place_only"
        stat[tier] += 1
        prev = area_tier.get(r["area_id"])
        if prev is None or TIER_RANK[tier] > TIER_RANK[prev]:
            area_tier[r["area_id"]] = tier
        meta[r["area_id"]] = (r["area_name"], r["province_code"])
        out.append(
            {
                "area_id": r["area_id"], "area_name": r["area_name"],
                "province_code": r["province_code"], "area_status": r["status"],
                "policy_id": r["policy_id"], "rel": r["rel"], "tier": tier,
                "policy_title": (r["title"] or "")[:70], "local_path": r["local_path"] or "",
            }
        )

    print("\n== 按链接 ==")
    for t in TIER_ORDER:
        if stat[t]:
            print(f"  {t:10s} {stat[t]:5d}  {stat[t]/len(rows)*100:5.1f}%")
    named = sum(stat[t] for t in ("exact", "core", "stripped", "tail", "segments"))
    weak = stat["place_only"]
    bad = stat["missing"] + stat["no_text"]
    print(f"  —— 正文点名片区（强依据）{named} = {named/len(rows)*100:.1f}%")
    print(f"  —— 仅出现县镇地名（弱依据）{weak} = {weak/len(rows)*100:.1f}%")
    print(f"  —— 完全无关（疑似挂错）{bad} = {bad/len(rows)*100:.1f}%")

    print("\n== 按片区（取最优链接）==")
    ts = Counter(area_tier.values())
    na = len(area_tier)
    for t in TIER_ORDER:
        if ts[t]:
            print(f"  {t:10s} {ts[t]:5d}  {ts[t]/na*100:5.1f}%")
    no_named = sum(v for k, v in ts.items() if k not in ("exact", "core", "stripped", "tail", "segments"))
    print(f"  没有「政策点名」支撑的片区：{no_named} / {na} = {no_named/na*100:.1f}%")

    prov = defaultdict(Counter)
    for aid, t in area_tier.items():
        prov[meta[aid][1][:2]][t] += 1
    print("\n== 分省：点名率最低的 12 个省 ==")
    rank = []
    for p, c in prov.items():
        n = sum(c.values())
        good = sum(c[t] for t in ("exact", "core", "stripped", "tail", "segments"))
        rank.append((good / n, p, n, good, c))
    for rate, p, n, good, c in sorted(rank)[:12]:
        print(f"  {p}  {good:3d}/{n:3d} = {rate*100:5.1f}%   弱{c['place_only']:3d} 无关{c['missing']:3d}")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with io.open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        print(f"\n已写 {args.csv}（{len(out)} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
