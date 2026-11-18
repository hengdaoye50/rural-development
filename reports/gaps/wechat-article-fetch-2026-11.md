# 公众号正文采集：链路打通与实测（2026-11，第二轮）

> 承接 `reports/gaps/media-leads-2026-11.md`。第一轮只到「搜狗结果页摘要」，
> 本轮 OpenCLI 扩展连通后，把**正文**这一环打通了。结论：链路可用，但产出的是线索不是证据。

## 一、环境状态转折

| 时间 | `opencli doctor` | 可用性 |
|---|---|---|
| 第一轮 | Extension: not connected、Connectivity failed | 只有 HTTP 直读结果页 |
| 本轮 | **Extension: connected (v1.0.27)**，profile `73xtmtqn` | 完整链路可用 |

关键前提：**Chrome 必须在运行**。本机一度只跑 Edge，daemon 起着但扩展连不上——
不是装没装的问题，是浏览器没开。

## 二、四步链路与两个坑

```
① opencli weixin search "<县> 片区 乡村振兴"     → 结果列表（标题/摘要/日期）
② opencli browser main open "<搜狗跳转链>"        → 解析出 mp.weixin.qq.com 直链
③ opencli browser main state                     → 判失效（隐私设置/已删除/违规）
④ opencli browser main eval "#js_content.innerText" → 取正文，自己写 .md
```

**坑一：`opencli web read` 读不了公众号正文。** mp.weixin 的 `src=11&timestamp=&signature=`
是一次性签名 URL，二次 fetch 只拿到 259 字节空壳。必须走 ④，从**已打开页面**取文本。
（第一轮手动试过一次 `web read` 成功，是因为那是该 URL 的首次请求。）

**坑二：导出文件互相覆盖。** 页面标题未就绪时 opencli 一律写成 `微信公众平台.md`，
连跑 5 篇只剩最后 1 篇。现按「序号-标题」自建文件名。

## 三、实测结果

| 指标 | 结果 |
|---|---|
| 现场搜索→打开→取正文（沁水县 4 篇） | **3 篇成功**（8811 / 2642 / 2979 字节），1 篇 `body_too_short` |
| 复用旧线索链接（5 篇） | 2 篇 `unresolved`、3 篇空壳——**签名链有时效，不能复用** |
| 失效原因分布 | 作者隐私设置、已被发布者删除、正常可读，三种都遇到 |
| 单篇耗时 | 约 8–12 秒（open + state + eval） |

**操作规则**：必须「搜索→立即打开→立即取文」，不能先存链后续再取。
所以 `media_leads.py`（批量存链）与 `wechat_fetch.py`（取正文）不能异步衔接使用，
正确用法是 `wechat_fetch.py --query "<县> 片区" --top N` 一条龙跑。

## 四、抽出来的东西，以及一个冷水

沁水县那篇抽到三个单元名：**「百里画廊」土沃农旅片区、「沁河古堡」片区、郑庄片区**。

回库核对（`P140011` 2026 年沁水县政府工作报告）：

- 「土沃」命中，但语境是**土沃乡获评省级乡村旅游重点乡镇**，不是片区
- 「郑庄」命中，但语境是**郑庄 3 座现代化矿井**，不是片区
- 「沁河古堡」「百里画廊」**完全没有**

也就是说：**媒体叫法在县级官方文本里查不到。** 这正是此前判定的「湖北/河南/天津模式」
在山西的复现——片区名活着报道里，官方文件只写乡镇。

按口径卡，这三条只能记 `待核`，不能进 `primary`/`support`。要转正，得找到县级
设立/规划/名单文件；找不到就登记「媒体有、官方无」。

## 五、这对「全国铺开」意味着什么

- **技术上可行**：单篇 8–12 秒，一条龙跑一县 3 篇约 40 秒
- **但要接受三个折损**：签名链不能复用（不能预跑清单）、部分文章不可读、
  抽出的名字多数拿不到官方依据
- **所以它的定位仍是「缺口定位器」**：告诉你「这个县有片区、大概叫什么」，
  然后由人去 `.gov.cn` 找文件。把它当证据源会直接把库的论点炸掉

## 六、脚本

```powershell
# 一条龙：搜索 → 打开 → 取正文（推荐用法）
& $env:MIMO_PYTHON scripts/wechat_fetch.py --query "沁水县 片区 乡村振兴" --top 4

# 复用线索（只适合刚生成的线索，链接会过期）
& $env:MIMO_PYTHON scripts/wechat_fetch.py --from-leads 5
```

产物：正文 `data/stage/candidates/wechat-md/{序号}-{标题}.md`，
清单 `data/stage/candidates/wechat-fetch-{date}.csv`（含 status：ok / privacy_blocked /
deleted / body_too_short / unresolved）。
