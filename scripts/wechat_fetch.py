"""把「搜狗线索 → 公众号直链 → 正文 Markdown」固化成流水线（只读、匿名）。

依赖 OpenCLI Browser Bridge（daemon + Chrome 扩展）。它比纯 HTTP 强在两点：
1. 能把搜狗的临时跳转链解析成 `mp.weixin.qq.com` 直链（HTTP 直取会被 antispider 拦）
2. 能导出正文 Markdown（`opencli web read`）

实测失效原因（必须记录，不能当成「没内容」）：
- 作者隐私设置 → 页面显示「根据作者隐私设置，无法查看该内容」
- 已被发布者删除 → 「该内容已被发布者删除」

边界：公众号不是 `.gov.cn`，按 `docs/07` 不得进 `policy` 层；产物只作线索与 `source` 候选。

    python scripts/wechat_fetch.py --from-leads 8
    python scripts/wechat_fetch.py --query "昌邑 片区 乡村振兴" --top 3
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEADS_DIR = ROOT / "data" / "stage" / "candidates"
MD_DIR = LEADS_DIR / "wechat-md"
MANIFEST = LEADS_DIR / f"wechat-fetch-{date.today().isoformat()}.csv"

BLOCKED_MARKS = {
    "privacy_blocked": "根据作者隐私设置",
    "deleted": "该内容已被发布者删除",
    "violation": "此内容因违规无法查看",
}


def run(args: list[str]) -> str:
    # opencli 在 Windows 上是 scoop 的 .ps1/.cmd 包装，subprocess 直接调用找不到可执行文件，
    # 必须经 shell；参数里没有用户可注入的元字符（URL 由我们自己拼），故 shell=True 安全
    cmd = subprocess.list2cmdline(args)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return (r.stdout or "") + (r.stderr or "")


def open_link(url: str) -> str:
    out = run(["opencli", "browser", "main", "open", url, "--window", "background"])
    return out


def state() -> tuple[str, str]:
    """返回 (当前 URL, 页面文本片段)"""
    out = run(["opencli", "browser", "main", "state"])
    m = re.search(r"^URL:\s*(\S+)", out, re.M)
    return (m.group(1) if m else ""), out


def main(argv: list[str]) -> int:
    MD_DIR.mkdir(parents=True, exist_ok=True)
    targets: list[dict[str, str]] = []

    if "--query" in argv:
        q = argv[argv.index("--query") + 1]
        top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 3
        out = run(["opencli", "weixin", "search", q, "--page", "1", "--limit", str(top),
                   "--window", "background", "--site-session", "ephemeral",
                   "--keep-tab", "false", "-f", "json"])
        try:
            data = json.loads(out[out.index("["): out.rindex("]") + 1])
        except Exception:                       # noqa: BLE001
            rows = re.findall(r"title:\s*(.+)\n.*?url:\s*>-?\s*\n?\s*(\S+)", out, re.S)
            data = [{"title": t.strip(), "url": u} for t, u in rows]
        targets = [{"query": q, "title": d.get("title", ""), "url": d.get("url", "")} for d in data][:top]
    else:
        n = int(argv[argv.index("--from-leads") + 1]) if "--from-leads" in argv else 5
        src = sorted(LEADS_DIR.glob("media-leads-*.csv"))[-1]
        with src.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        for r in rows[:n]:
            targets.append({"query": r["query"], "title": r["title"], "url": r["url"]})

    print(f"待取 {len(targets)} 篇")
    out_rows = []
    for i, t in enumerate(targets, 1):
        open_link(t["url"])
        url, text = state()
        status, md_path = "unresolved", ""
        if "mp.weixin.qq.com" in url:
            for k, mark in BLOCKED_MARKS.items():
                if mark in text:
                    status = k
                    break
            else:
                status = "ok"
        if status == "ok":
            # 不能用 `web read` 二次 fetch：mp.weixin 的 src=11 签名 URL 是一次性的，
            # 二次请求只会拿到空壳（实测 259 字节）。必须从**已打开的页面**取文本。
            js = ("(()=>{const e=document.querySelector('#js_content')||document.body;"
                  "return JSON.stringify({t:document.title,x:e.innerText||''})})()")
            out = run(["opencli", "browser", "main", "eval", js])
            try:
                payload = json.loads(out[out.index("{"): out.rindex("}") + 1])
            except Exception:                     # noqa: BLE001
                payload = {}
            text = (payload.get("x") or "").strip()
            title = (payload.get("t") or t["title"]).strip()
            if len(text) < 200:
                status = "body_too_short"
            else:
                slug = re.sub(r'[\\/:*?"<>|\s]+', "", title)[:40] or "untitled"
                dest = MD_DIR / f"{i:02d}-{slug}.md"
                dest.write_text(f"# {title}\n\n> 来源: {url}\n\n{text}\n",
                                encoding="utf-8", newline="\n")
                md_path = str(dest.relative_to(ROOT)).replace("\\", "/")
        print(f"  [{i}/{len(targets)}] {status:16s} {t['title'][:34]}")
        out_rows.append({"query": t["query"], "title": t["title"], "mp_url": url,
                         "status": status, "md_path": md_path})

    ok = sum(1 for r in out_rows if r["status"] == "ok")
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "title", "mp_url", "status", "md_path"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\n成功 {ok}/{len(out_rows)}；清单 -> {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
