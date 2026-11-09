"""One-off TJ01 helper: fetch a gov page, extract main text, save as Markdown.

Usage: python tj01_save.py <url> <out_name> [title]
"""
import io
import os
import re
import sys

sys.path.insert(0, "scripts/legacy")
from tj01_grep import text_of  # noqa: E402
from tj01_probe import fetch  # noqa: E402

TXT_DIR = os.path.join(os.environ.get("TEMP", "."), "tj01", "txt")

CUT_AFTER = [
    "扫一扫在手机打开当前页",
    "【打印本页】",
    "【关闭页面】",
    "责任编辑",
    "附件下载",
    "分享到：",
]
DROP = [
    "繁體", "无障碍", "关爱版", "进入关怀模式", "首页", "政务公开", "政务服务",
    "政民互动", "走进", "网站地图", "使用帮助", "主办单位", "承办单位", "版权所有",
    "网站标识码", "ICP备", "公网安备", "地址：", "邮编", "QQ空间", "豆瓣网",
    "微信分享", "新浪微博", "当前位置", "位置：", "字号：", "大 中 小",
    "中国政府网", "农业农村部", "市农业农村委", "市文化和旅游局", "各区", "重点链接",
    "返回顶部", "移动门户", "咨询电话", "政务邮箱", "新媒体矩阵", "文件下载",
    "关于我们", "联系我们", "网站声明", "网站纠错", "建议升级浏览器",
]


META_LABELS = [
    "索引号", "发布机构", "发文字号", "主题分类", "成文日期", "发布日期",
    "有效性", "联合发文单位", "修改和废止依据", "名称",
]


def trim_head(body, title):
    lines = body.split("\n")
    last_meta = -1
    for i, ln in enumerate(lines):
        s = ln.strip()
        if any(s.startswith(lb) or (lb in s and len(s) < 40) for lb in META_LABELS):
            last_meta = i
    if last_meta > 0:
        return "\n".join(lines[last_meta + 1:])
    for i, ln in enumerate(lines):
        if ln.strip().startswith("来源") or ln.strip().startswith("来源："):
            return "\n".join(lines[i + 1:])
    if title:
        idx = body.rfind(title)
        if idx > 0:
            return body[idx + len(title):]
    return body


def clean(url, title=""):
    body = text_of(fetch(url))
    body = trim_head(body, title)
    for marker in CUT_AFTER:
        i = body.find(marker)
        if i > 500:
            body = body[:i]
            break
    lines = []
    for ln in body.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if len(s) < 30 and any(d in s for d in DROP):
            continue
        lines.append(s)
    return "\n\n".join(lines)


if __name__ == "__main__":
    url, name = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    text = clean(url)
    if title and not text.startswith(title):
        text = f"# {title}\n\n{text}"
    os.makedirs(TXT_DIR, exist_ok=True)
    path = os.path.join(TXT_DIR, name + ".md")
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text + "\n")
    print(f"saved {path} chars={sum(1 for _ in text)} head={text[:200]!r}")
