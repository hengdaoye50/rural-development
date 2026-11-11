"""Repair full_text on the three 沂水 records whose extraction caught chrome."""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _sd09_fetch as F

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "POL-SD09-policy.jsonl")

TRAIL_RE = re.compile(r"关闭窗口|Word版下载|PDF版下载|爱山东APP|网站标识码|主办：|承办：|"
                      r"举报邮箱|纠正此文的错误|纠正文|返回顶部|^中国政府网$|^微信公众号$|^沂水首发$")
CRUMB_RE = re.compile(r"^(首页|正文|法定主动公开内容|政务要闻|微博|微信|微信)$")
SEP_RE = re.compile(r"^[大中小|\s]+$")
TITLE_ROW_RE = re.compile(r"(题|标)\s*\xa0*\s*：")

HAND42 = """# 市农业农村局来我县调研乡村振兴和美丽乡村示范片区建设工作

3月29日，市农业农村局党组书记、局长王康亮带队到我县调研乡村振兴和美丽乡村示范片区建设工作。县委副书记、县长赵明，县委副书记、诸葛镇党委书记刘铭等陪同参加。

王康亮一行首先到黄山铺镇尧崖头村和寺前官庄村美丽乡村示范片区现场调研，听取有关工作情况介绍。王康亮强调，要扎实做好农村人居环境整治提升工作，谋划好、实施好美丽乡村建设。黄山铺镇扎实推进美丽乡村建设，融入地理、人文、产业特点，狠抓基础设施、生态绿化、人居环境提升，现有省级美丽乡村4处、市级美丽乡村3个。目前，正在建设市级美丽乡村连片1处（8个村）、美丽乡村示范区1处（48个村），初步确定「三河同秀、四带共赢、五路并进」的美丽乡村示范区整体发展思路，计划2年时间优化全镇美丽乡村「一盘棋」整体布局，打造特点鲜明的「一河一题、一村一品」美丽乡村示范区。

随后，王康亮一行来到院东头镇昆润生姜产业园和西墙峪村乡村振兴示范片区现场，详细了解产业强镇建设工作。王康亮要求，要高质量推进农业农村现代化发展，以产业振兴推动乡村振兴，实实在在提升群众获得感、幸福感。院东头镇乡村振兴示范片区坚持整镇域推进，涵盖镇域内所有村庄，已建成及正在建设的产业项目12个。示范区以建设农文旅融合发展为目标，以绿色生姜种植、流通、深加工为基础，以旅游景区、产业项目建设为带动，以合作社融合链接为纽带，绿色生态建设为底线，人才建设为支撑，组织建设为保障，打造成全国革命老区知名的乡村振兴示范样板。

县互联网信息安全服务中心 吴世翠

通讯员 沙泳君 聂高强"""


def reclean(txt):
    lines = [ln.strip() for ln in txt.split("\n")]
    # 去掉正文起点之前的导航与元数据表
    cut = 0
    for i, ln in enumerate(lines[:40]):
        if TITLE_ROW_RE.search(ln):
            cut = i + 1
    lines = lines[cut:]
    # 去掉正文终点之后的页脚
    for i, ln in enumerate(lines):
        if TRAIL_RE.search(ln):
            lines = lines[:i]
            break
    out = []
    for ln in lines:
        if CRUMB_RE.match(ln) or SEP_RE.match(ln):
            continue
        out.append(ln)
    res = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return res


def main():
    recs = []
    with io.open(TARGET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))

    changed = 0
    for o in recs:
        url = o.get("url", "")
        if url.endswith("/229654.htm"):
            o["full_text"] = HAND42
            changed += 1
            print("HAND-FIXED:", url)
        elif url.endswith("/357744.htm") or url.endswith("/456770.htm"):
            o["full_text"] = reclean(o["full_text"])
            changed += 1
            print("RECLEANED %5d chars: %s" % (
                len(re.sub(r"\s", "", o["full_text"])), o["title"][:40]))

    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as f:
        for o in recs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("records:", len(recs), "changed:", changed)


if __name__ == "__main__":
    main()
