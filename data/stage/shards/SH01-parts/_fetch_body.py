import json, re, sys, urllib.request, os, html
from pathlib import Path

PARTS = Path(r"D:\CODEX\全国乡村片区化数据库\data\stage\shards\SH01-parts")
TEXTDIR = PARTS / "text"
TEXTDIR.mkdir(parents=True, exist_ok=True)

HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}

DOCS = {
    "05": dict(url="https://www.pudong.gov.cn/zwgk/azt_zcfg/2026/168/356354.html",
               start=r"区各相关部门、各相关镇",
               end=r"网民留言"),
    "06": dict(url="https://www.jiading.gov.cn/infopublicity/communique/publicinformationdetails/709",
               start=r"各镇人民政府\s*[，,]\s*区政府各委",
               end=r"文件下载"),
    "07": dict(url="https://www.shanghai.gov.cn/nw12344/20250917/8873956951994f9aa013cf008cb5b5fd.html",
               start=r"各乡\s*[、,]\s*镇人民政府",
               end=r"分享："),
    "08": dict(url="https://www.shanghai.gov.cn/xcfz-gqwj13/20260803/819e262b6c1445a7b56fbe3a21eaa73e.html",
               start=r"各镇人民政府、街道办事处、区政府各部门",
               end=r"分享："),
    "09": dict(url="https://www.shanghai.gov.cn/gwk/search/content/e2bf9d78-eb58-4e2f-89c7-9216e9723a9d",
               start=r"印发日期",
               end=r"分享："),
}

KEYWORDS = {
    "财政": ["财政", "补助", "奖补", "资金", "专项"],
    "土地": ["用地", "供地", "土地综合整治", "减量化", "建设用地"],
    "组织": ["领导小组", "专班", "驻村", "党组织", "牵头"],
    "考核": ["考核", "评估", "评价", "督查", "验收"],
    "规划": ["规划编制", "控规", "郊野单元", "规划引领", "两图一表"],
    "人才": ["人才", "高素质农民", "培训", "乡村建筑师", "工匠"],
    "金融": ["金融", "信贷", "保险", "贷款", "担保"],
    "产业": ["产业", "招商", "运营", "集体经济"],
    "数字": ["数字化", "数字乡村", "智慧", "物联网", "一网统管"],
}


def fetch(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


def strip_html(h):
    h = re.sub(r"<script[\s\S]*?</script>", " ", h, flags=re.I)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h, flags=re.I)
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r"</(p|div|tr|h1|h2|h3|h4|li|td|br)>", "\n", h, flags=re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    h = h.replace("\u00a0", " ").replace("\u3000", " ")
    lines = []
    for ln in h.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def main():
    passno = sys.argv[1] if len(sys.argv) > 1 else "1"
    for key, cfg in DOCS.items():
        try:
            text = strip_html(fetch(cfg["url"]))
        except Exception as e:
            print(f"[{key}] FETCH_ERR {cfg['url']} -> {e}")
            continue
        m1 = re.search(cfg["start"], text)
        body = text[m1.start():] if m1 else text
        if cfg.get("end"):
            m2 = re.search(cfg["end"], body)
            if m2:
                body = body[: m2.start()]
        (TEXTDIR / f"{key}.md").write_text(body, encoding="utf-8")
        han = len(re.findall(r"[\u4e00-\u9fff]", body))
        print(f"[{key}] chars={len(body)} han={han} url={cfg['url']}")
        print(f"  HEAD: {body[:90]!r}")
        print(f"  TAIL: {body[-90:]!r}")
        if passno == "2":
            for inst, kws in KEYWORDS.items():
                hits = []
                for kw in kws:
                    for m in re.finditer(kw, body):
                        hits.append(body[max(0, m.start() - 18): m.start() + 22].replace("\n", " "))
                        break
                if hits:
                    print(f"  {inst}: " + " | ".join(hits[:4]))
        print()


main()
