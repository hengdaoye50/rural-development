"""验证搜狗微信的跳转链能否解析出 mp.weixin.qq.com 直链。

搜狗结果给的是 /link?url=... 临时链，需要拿它换文章直链才能读正文。
常见做法：跟随跳转，页面里用 JS 拼出 url（有 `url += '...'` 片段）。
本脚本尝试直接取 mp.weixin 链接，失败则如实报告。
"""
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url, referer="https://weixin.sogou.com/"):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": referer, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
        final = r.geturl()
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc), final
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore"), final


def main(link: str) -> int:
    html, final = get(link.replace("&amp;", "&"))
    print("最终 URL:", final[:120])
    m = re.search(r"https?://mp\.weixin\.qq\.com/s\?[^'\"\s]+", html)
    if m:
        print("直链:", m.group(0)[:140])
        return 0
    frags = re.findall(r"url \+= '([^']*)'", html)
    if frags:
        print("JS 片段拼接命中", len(frags), "段：", "".join(frags)[:160])
        return 0
    if "请输入验证码" in html or "antispider" in html or "异常" in html:
        print("被反爬拦截（验证码/异常页）")
        return 2
    print("页面长度", len(html), "未见直链；前 300 字：")
    print(re.sub(r"<[^>]+>", " ", html)[:300])
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
