# -*- coding: utf-8 -*-
"""组装并追加写入 POL-ZJ03-policy.jsonl。
用法: python _zj03_emit.py 1|2|3|all
"""
import sys, os, re, json, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\CODEX\全国乡村片区化数据库\data\stage"
TXT = D + r"\_zj03_raw\txt"
OUT = D + r"\POL-ZJ03-policy.jsonl"
FETCHED = "2026-11-05"

DROP = re.compile(r"^(打印|关闭|打印 关闭|【返回顶部】.*|【打印本稿】.*|字体：\[ 大 中 小 \]|"
                  r"浏览次数：.*|扫一扫.*|分享到.*|-)+\s*$")


def clean(md):
    lines = []
    for l in md.split("\n"):
        s = l.strip()
        if DROP.match(s):
            continue
        if s.startswith("网站首页") and ">" in s:
            continue
        lines.append(s)
    seen, out = set(), []
    for l in lines:
        k = l.strip()
        if len(k) > 25:
            if k in seen:
                continue
            seen.add(k)
        out.append(l)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt


def load_meta():
    m = []
    for i in (1, 2, 3, 4):
        p = D + rf"\_zj03_meta{i}.py"
        spec = importlib.util.spec_from_file_location(f"m{i}", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        m += mod.META if i == 1 else getattr(mod, f"META{i}")
    return m


def build(rec):
    _id = rec["id"]
    p = os.path.join(TXT, _id + ".json")
    d = json.load(open(p, encoding="utf-8"))
    body = clean(d["body_md"])
    if not body:
        raise SystemExit(f"{_id}: EMPTY BODY")
    chars = len(re.findall(r"[\u4e00-\u9fff]", body))
    out = {k: v for k, v in rec.items() if k != "id"}
    out["url"] = d["url"]
    out.setdefault("valid_state", "现行有效")
    out["summary"] = out.get("summary", "")
    out["fetched_at"] = FETCHED
    out["full_text"] = body
    out["full_text_chars"] = chars
    out.setdefault("areas", [])
    out.setdefault("events", [])
    return out


def main():
    meta = load_meta()
    recs = [build(r) for r in meta]
    # 每次全量重写，保证幂等；但先校验全部成功再落盘
    with open(OUT, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"WROTE {OUT} n={len(recs)}")
    for r in recs:
        print(f"  {r['full_text_chars']:5d}字 | {r['county_code'] or '-'} | {r['title'][:52]}")


if __name__ == "__main__":
    main()
