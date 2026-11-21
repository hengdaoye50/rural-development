# 交接文件（HANDOVER）

> **给接手的新 harness：先读这一份，再读 `CLAUDE.md`（约束权威）。**
> 本文件不重复 `CLAUDE.md` 的规则条文，只交代**当前状态、已完成、未完成、陷阱**。
> 最后更新：2026-11-18｜快照：`data/db/片区库.sqlite3`（4.4 MB）

---

## 0. 三十秒理解这个项目

统计中国大陆 31 省、**县/区以下**、以「片区」为单位推进乡村振兴的实践，建成可核验的档案库。

**一句话现状**：政策全文层已完备（1 702 份 / 1 038.3 万汉字，全部可校验）；片区实体层是**建档式抽样**（主统计 556 个，浙江占 45%）；**空间锚定（村级归属）仍为 0**，是当前最大短板。

**这个库不是**：全国普查、政策汇编、示范县镇村名录、片区实体生命周期台账。

---

## 1. 当前精确数字（快照 2026-11-18）

| 层 | 数据 |
|---|---|
| `area` 总行 | **1 351**（active 1 448 = 计入 1040 + 待核 408；superseded 11；withdrawn 2） |
| `belt` 象征单元 | 118（去跨表重名后计 100） |
| `policy` 政策 | **1 702**（A 级 496），全文 **10 382 909 汉字** |
| `area_policy_map` | **1 981**（primary 625 / support 595 / mention 761） |
| `event` 事件 | 731（覆盖 455 个片区，**撤销类 0 条**） |
| `source` 来源 | 478（463 有本地快照，15 显式无快照） |
| `region` 区划 | 3 229（省 34 / 市 339 / 县 2 856） |
| `macro_unit` 命名单元 | **1 353** |

**口径分层（在册非待核 1040）**：A 617｜B 12｜C 216｜D 24｜E 171

| 对外口径 | 数值 | 用途 |
|---|---|---|
| **主统计 A+B** | **629** | 论文主分析样本；可归时 + 可归因 |
| 宽统计 A+B+C | 845 | 含时间不详，**不得进年份分布** |
| 在册非待核 | 1040 | 全部在册 |
| 案例池（四要素≥3） | 235 | 可写案例；浙江占 112（48%） |
| 深描子集（四要素全备） | 41 | 单案例长文 |
| 命名单元 | 1 353 | 只用于量级与分布 |

**设立方式（主统计内）**：`roster` 名单型 176｜`deployment` 部署型 308。
**县覆盖**：有命名单元的县 671／2 856（22.3%）；可信记录口径 **521／2 856 = 18.2%**。
县覆盖有 4 套口径并存，报数前先看 `reports/qa/接手审校-2066-11-18.md` §三 A。

---

## 2. 五分钟自检（先跑这五条，确认世界没变）

```powershell
cd D:\CODEX\全国乡村片区化数据库
$env:MIMO_PYTHON            # 应为 Runtime\win32-x64\python\Lib（Python 3.12.13）
& $env:MIMO_PYTHON scripts/build_db.py        # 重建库（幂等）
& $env:MIMO_PYTHON scripts/validate_db.py     # 期望：issues=0 warnings≈2234
& $env:MIMO_PYTHON scripts/health_report.py   # 主统计应为 629
& $env:MIMO_PYTHON scripts/report_db_stats.py # 全量总览
```

**判据**：`issues=0` 且主统计 556。若主统计对不上，先看 `git log` 有没有新提交改变了数据，
再看 `docs/01` §10 口径卡有没有被改。

---

## 3. 目录与文件职责（只列关键的）

```
CLAUDE.md                     约束唯一权威：目录红线、命名、决策日志、全部命令
HANDOVER.md                   本文件：状态交接
docs/00-整体规划.md            里程碑、当前进度与偏差（含"停止按省摊派采集"的决定）
docs/01-概念界定.md            §10 统计口径卡、§11 双层口径（M/P）——所有数字的地基
docs/02-数据字典.md            字段唯一权威（含 setup_kind、is_core）
docs/07-政策层.md              政策层白名单（只收 .gov.cn）与字段
docs/09-研究数据与边界声明.md   论文可直接引用的数据段（N=471，2026-11-18 已同步）
data/raw/{ABBR}/             证据原件，只追加不覆盖，路径=data/raw/SD/20260513-slug/原文.md
data/stage/batches/          ingest 待入库 JSONL（POL-{省码}{序号}-policy.jsonl）
data/stage/candidates/       候选名单（area-roster-{ABBR}.csv、media-leads-*.csv、wechat-md/）
data/clean/by_province/      分省 CSV（并发写这里，再 merge）
data/clean/province_roster.csv 省级名单台账（31 省名单状态/官方数 vs 库内数）
data/clean/city_roster.csv   市级名单台账（浙苏鲁 40 市）
data/db/片区库.sqlite3       主库，禁止手改，由 build_db 从 clean 重建
scripts/                     113 个管线脚本（见 §5）
reports/qa/                  校验、审计、口径对账
reports/gaps/                缺采县、公众号线索、通道实测
reports/pilot/               批次与名单入库小结
```

**注意**：`docs/01` §10 口径卡与 `README`、`docs/09` 的数字必须随快照重算，
2026-11-18 刚做过一次全量同步（见 `reports/qa/接手审校-2026-11-18.md` §五）。

---

## 4. 数据管线（最短路径 + 必踩的坑）

```
采集 → data/stage/batches/*.jsonl → ingest_policy.py → clean/by_province/*.csv
     → merge_by_province.py → build_db.py → validate_db.py → 各报告脚本
```

**三条铁律**：

1. **任何「删除」都要同时处理两处**：`merge_by_province` 对 map 表是「by_province 优先 + master
   补缺」，只删 by_province 会被 master 补回；`ingest_policy --purge` 只清库、不清 JSONL。
2. **`area` 是实体表**，改它只写 `by_province`（merge 会重建 master）；**map 表**必须两处同改。
3. **新增字段要三处同改**：`docs/02` + `build_db` DDL + by_province CSV。漏一处就是静默丢数据。

---

## 5. 已完成，不要重做

### 口径与规则
- 统计口径卡（`docs/01` §10）：四界一快照 + 五组互斥分层，落地为视图 `area_caliber`
- 双层口径（§11）：M 宏观层 1 353 / P 政策层 556，不共用分母
- 「有依据」只认 `primary`/`support`，`mention` 单列——**旧数字 96.8%／80.8% 全部作废**
- `setup_kind` 分名单型/部署型（含"名单藏在附件表格里"的识别）
- 案例池口径（四要素取三）：235

### 数据清洗（都做过，别重跑）
- 占位区划码 15 条归位；region 补 14 个缺失市码；龙南双码去重
- `first_source_id` 悬空 5 条：3 条按 raw 复原、2 条撤回
- 数值字段污染 12 条清空（国道/省道编号、户数、地名被灌进 scale_*）
- 摘要按原文摘录回填 78 条（台账 `reports/qa/text-backfill-log.csv`）
- 浙江 13 条缺 `area_region_map` 行已补（`scripts/repair_area_region_map.py`）
- P4 待核 16 条逐条裁定已落地（`scripts/adjudicate_pending_areas.py`）
- **region 补 133 个地级市码**（`scripts/backfill_region_from_mca.py`，数据源为仓库内民政部代码表）
- T1 24 县 + T2 49 县核查完成，关闭台账 `data/stage/candidates/gap-checks-*.csv`
- 新增 `scripts/check_doc_caliber.py`：文档口径数字与库内值不一致时非零退出
- `validate_db` 已加五项硬检查：占位码、悬空城市码、引用悬空、数值字段须为整数、
  active 片区缺区划归属行

### 文稿
- `reports/统计总览-2026-11.md`（全库七节统计，脚本生成）
- `reports/数据库建设情况概述-2026-11.md`（对外概述，含短板与边界）
- `reports/qa/provincial-targets.md`（省级官方自述数锚点：山东 2070/93/100、江苏 40、江西 50…）
- `README.md`（已按现状重写）

---

## 6. 未完成（按优先级，带具体落点）

### P1 空间锚定（最大短板，做别的都绕不开它）
- `area_region_map` 的 **village 级记录为 0 条**；有 `scale_villages` 532 条、`town_codes` 594 条
- **真正的卡点不是没写村名**：`cover_desc` 里点名具名村的记录有 **705 条**
  （如 A110001「大周各庄村为示范村、小周各庄等 5 村为提升村」）
- 卡在编码：`region` 表只有省/市/县三级（34/206/2856），**没有 town/village 行**，
  而 `area_region_map.region_code` 有外键语义。`docs/02` 允许 level 取 town/village，
  但**没有本地码编码规则**。所以 P1 第一步是定村级编码方案，不是填数据
- 影响：规模分析、地图（M6）、"片区覆盖几村"这类描述全卡在这里

### P2 114 个「证据已在手」的县（**2026-11-18 已清空 T1/T2**）
- 清单：`reports/gaps/coverage-gaps.md` / `.csv`（现只剩 T3 41 县）
- T1 24 县：逐县读本级文件，**全部查无具名单元**（城市控规片区/无专名示范带/园区先行区），
  见 `reports/gaps/T1-24县核查-2026-11-18.md`
- T2 49 县：新增 9 条（广西田园综合体 5、辽宁细河区段 1、江苏射阳段 1、待核 2），
  41 县关闭（邻县点名/城市片区/名单类型不符），见 `reports/gaps/T2-49县核查-2026-11-18.md`
- 关闭台账：`data/stage/candidates/gap-checks-*.csv`，`find_coverage_gaps` 会跳过
- 做法已固化：逐份读本地 `data/raw` 原文 → 建 `area-roster-{ABBR}.csv` → `ingest_area_roster.py`

### P3 浙江 6 份名单的列结构登记（合计约 70 行）
- P330514 黄岩（18 行）、P330052 海宁（12）、P330448 衢江（11）、P330064 乐清（10）、
  P330478 淳安（7）、P330002/4/8 湖州（16）
- 每份在 `scripts/roster_from_policy_table.py` 的 `FORMS` 里加一条列映射即可
- 也可直接改 `--generic` 的匹配规则（现规则：名称须以片区类通名结尾）

### P4 待核与无依据的处置（**2066-11-18 已执行一轮，原「15 条快赢」前提已证伪**）
- 待核从 227 降到 **219**：16 条逐条裁定，8 条升级（3 条同时改名对齐官方表述）、
  2 条 rel 纠错（primary→mention/support）、6 条维持待核并写明卡点
- 关键改名的 3 条：`吴中片区→东太湖宜居宜业和美乡村片区`、`湖埠片区→双浦环铜鉴湖·生态旅居片区组团`、
  `金山银海片区→金山银海·和美金城片区`
- 裁定表：`data/stage/candidates/pending-decisions-2026-11-18.csv`；落地脚本
  `scripts/adjudicate_pending_areas.py`（幂等，`--dry-run` 可看）
- 剩余 219 条的卡点分类：媒体单源 172、名称/规模/实体认定 47
- 无依据 233（E 220 + D 组无依据 13）：多数是「媒体名 vs 官方名」不一致（湖北/河南/天津模式），
  要么改名对齐，要么登记"媒体有、官方无"

### P5 其他省的官方锚点
- 现只有山东/江苏/江西/绍兴/象山/济南。广东、河南、湖北、贵州四个大省缺锚点
- 贵州另有专项：应改采《省级集成示范试点名单》（用户已裁定）

### 已知硬缺口（可能无法补）
- 山东省委农办《关于推进乡村振兴片区建设的意见（试行）》**鲁农组办发〔2025〕2号**：文号确认，
  全文未公开，只能以引用关系登记（`reports/qa/provincial-targets.md` §五）
- 全国/全省总量不可得：官方"累计"数与库内"命名事件"单位不可通约，**不要试图对齐**

---

## 7. 红线（最易踩的十条）

1. 中文内容只用 `write`/`edit` 工具改；**PowerShell 读写中文文件会按 GBK 重写导致乱码**（已踩多次）
2. `data/clean` 与 `data/db` 禁止手改，一切走脚本
3. 收集 `.gov.cn` 之外的来源（公众号/媒体/融媒）**不得进 `policy` 层**，只能做线索或 `source`
4. 不得绕过反爬（换 IP/轮换 UA/模拟点击）；公众号文章失效就如实记 `privacy_blocked`/`deleted`
5. 名称、时间、村数取不到就留空，**不猜、不用区间或概数糊**
6. 摘要一律**逐字摘原文**，摘不到就空着——不准写"看起来像摘要"的话
7. 派生字段的判据**不能用宽泛词**（裸「公布」曾把 46 条"规划批后公布"误判成名单型）
8. 报"片区数量"必须指明是哪个口径（主统计 556 / 宽 743 / 在册 987 / 命名单元 1 353）
9. git 提交需显式授权；`data/raw` 是唯一证据副本，**永不 `git reset --hard` / `git clean`**
10. 删文件前先问；自己本轮生成的临时产物可以清

---

## 8. 最近三轮做了什么（上下文）

1. **河北省级名单入库**（`b04b75f`）：P130001 附件 3 是 29 条片区资金安排表，新增 23 条、覆盖 17 新县；
   顺带修 `setup_kind`：名单常藏在方案附件里，标题看不出 → 加"原文含 ≥5 行含片区表格行即 roster"
2. **全库表格扫描**（`819dc56`）：全库只有 17 份含片区表格的政策；从中入库绍兴 P330437 六条。
   **教训**：上一轮按"命中零单元县数"排的"高杠杆文件"多数不是名单（云南那份是示范乡镇名单、
   陕西是报道、武汉是方案）——命中县数只能排阅读顺序，不等于有名单
3. **公众号通道**（`15afc73`）：OpenCLI Browser Bridge 打通，但 mp.weixin 签名链一次性，
   必须"搜索→立即打开→立即取文"，且 1/3 文章因隐私设置或删除读不到
4. **接手审校**（2066-11-18，未提交）：修 `health_report` 硬编码 854、补 13 条浙江区划
   归属行并加 validate 硬检查、全量同步 README/`docs/00`/`docs/01`/`docs/09` 口径数字、
   重跑缺口清单。详见 `reports/qa/接手审校-2026-11-18.md`
5. **P4 待核裁定**（2066-11-18 二，未提交）：16 条逐条读原文裁定，升级 8 条（3 条改名对齐
   官方表述）、rel 纠错 2 条、维持待核 6 条；待核 227→219，主统计 468→**470**。
   台账 `data/stage/candidates/pending-decisions-2026-11-18.csv`
6. **T1/T2 缺口核查**（2066-11-18 三，未提交）：T1 24 县全部查无；T2 新增 9 条
   （广西田园综合体 5 / 辽宁细河区段 / 江苏射阳段 / 两条待核）、关闭 41 县；
   有证据县 114→**41**（只剩 T3）。顺带补 region 133 个地级市码，
   并新增文档口径守卫 `check_doc_caliber.py`。详见 `reports/gaps/T2-49县核查-2066-11-18.md`
7. **省级层落实（两轮，2026-11-19/20，未提交）**：
   - 广东 130 条省级名单按媒体（C）建档（待核）、广西田园综合体补到 8/8、天津 12 条核对为完整
   - **省级名单台账进库**：新增 `province_roster` 表（31 省 × 名单状态/官方数/库内数），
     报告改由 `report_province_roster.py` 从表生成；`validate_db` 增加该表引用与数值检查
   - 新增脚本：`ingest_area_media_roster.py`、`report_level_distribution.py`、`report_province_roster.py`
   - 详见 `reports/省级名单台账.md`、`reports/片区层级分布.md`

---

## 9. 环境与依赖

| 项 | 状态 |
|---|---|
| `$env:MIMO_PYTHON` | **新 harness 里为空**。管线脚本纯 stdlib，用系统 Python 3.12 即可：`C:\Users\zjh22\AppData\Local\Programs\Python\Python312\python.exe` |
| pandas / openpyxl | 系统 Python **未装**；`export_excel.py` 等需要时用 `uv venv .venv` + `uv pip install pandas openpyxl` |
| `.venv-ocr` | 存在（RapidOCR + pypdfium2），扫描件 OCR 用 `.venv-ocr\Scripts\python.exe scripts/ocr_pdf.py` |
| `opencli` | v1.8.7，daemon 常驻；**Chrome 必须运行**且装 Browser Bridge 扩展才可用 |
| tinyfish MCP | 可用（搜索/取页面），token 效率高于自建 HTTP |
| git | 工作树干净，HEAD `a6d7709`；`data/db/*.sqlite3` 与 `data/stage/batches/` 已 gitignore |

**已知环境坑**
- `core.autocrlf=true` 且无 `.gitattributes`：重新 clone 会把 raw 的 LF 转 CRLF，
  导致 `sha256(file) != hash_sha256`。**尚未修**，属待办
- `opencli` 在 Windows 是 `.ps1` 包装：脚本内调用需 `shell=True`，直接 subprocess 会 `WinError 2`
- PowerShell 读中文 CSV/MD 按 GBK 解码，看到的会是乱码；判断内容一律用 `read` 工具，
  脚本内一律 `encoding='utf-8-sig'` + `sys.stdout.reconfigure(encoding='utf-8')`

---

## 10. 术语与口径速查

| 说法 | 含义 |
|---|---|
| 主统计 / A+B | 556。可归时（2022–2066 窗内或延续至今）+ 可归因（`primary`/`support`） |
| 宽统计 / A+B+C | 743。加时间不详，不进年份分布 |
| 在册非待核 | 987。含 D 组（口径外 24）与 E 组（无依据 220） |
| 命名单元 / M 层 | 1 353 = area 1 253 + belt 100（去跨表重名）。只看量级 |
| 案例池 | 235。四要素（覆盖可述/规模可知/有事件/时间精到月）取三 |
| `primary` | 文件直接设立、批复、命名该片区 |
| `support` | 文件点名支持/安排，但不是设立依据 |
| `mention` | 文件仅作案例或顺带提及，**不计入依据** |
| `roster` / `deployment` | 名单型设立 / 部署型设立（政府工作报告、规划点名部署） |
| 口径外（D 组） | 2022 前成立且 2023 后无任何政策或事件；不删记录，视图排除 |

---

## 11. 下一轮建议做什么

当前主线是**按层夯实数据**（用户 2026-11-19 定）：省级层已基本查清（见
`reports/省级名单台账.md`），正在做**市级层**（见 `reports/市级名单台账.md`）。
建议顺序：

1. 按 §2 跑自检；另跑 `repair_area_region_map.py --dry-run`、`adjudicate_pending_areas.py --dry-run`、
   `check_doc_caliber.py`，三者都应 0 改动 / 全部一致
2. **市级层（主线）**：
   - **宿迁**：《高质量建设宜居宜业和美乡村的实施方案》原文 → 8 个示范片区入库
   - **浙苏鲁其余 34 市**：逐市检索「市农业农村局 + 名单/公布/认定」，优先同类「样板片区/精品片区」
   - `city_roster` 扩到全国 333 个地级行政区（先补数据厚的省，再铺其余）
3. **省级遗留**：广东 130 条找 `.gov.cn` 原文（一次升级 130 条）；浙江 200 个组团片区是否另有名单
4. **P1 空间锚定**：`cover_desc` 点名具名村的记录 700+ 条，建 `area_village` 成员表（先 20 条试点）
5. **贵州口径复核**：集成示范试点是村层名单，与原裁定冲突，等用户裁定

**不要做**：按省摊派并行采集、全库正文正则抽片区名、把 T3 的「动态顺带提及」当设立依据。

**本轮经验与下一轮 SOP**：`reports/qa/经验教训-2026-11-21.md`（智能体并发 6/批、产出必须落文件、CSV 原子写、县区带前缀、附件抽取链）。
**市级名单优先级高于县级铺量**：一份市级名单 = 几条到几十条片区，且直接补上县以下实体。

9. **市级层落地（2066-11-20 二，未提交）**：40 市名单扫描（一市一智能体，结果落 `data/stage/candidates/city-roster-scan-2066-11-21.json`），city_roster 变为 matched 6 / partial 20 / count_only 8 / not_area 1 / none 5；青岛（第二批 8）、枣庄（20）、常州（11）三市名单按官方全文入库 39 条，主统计 477→**556**、宽 664→743、全量库 908→987。新增 `build_city_rosters.py`、`apply_city_roster_scan.py`、`upgrade_media_roster.py`

10. **市级层续（2026-11-21，未提交）**：青岛补齐 18/18（新增 P370341 首批 10 条，净增 2）；连云港按 连乡振〔2023〕3号 工作要点入库 4 条（石梁河跨县分建）；city_roster matched 11 / partial 15 / count_only 8 / not_area 1 / none 5；主统计 556、全量库 987、M 层 1438、县覆盖 637（可信 487）

11. **数据清洗 + 口径设计（2026-11-21 三，未提交）**：新增资产盘点/质量审计/批量修复三脚本，ERROR 172→0、WARN 390→203；待核升级 25 条使主统计 591、宽 792；新增 `docs/10-统计口径与数据库设计.md`（分析单元/分层维度/覆盖率分母/证据强度/落地路线 P0–P2）。详见 `reports/qa/数据清洗-2026-11-21.md`

12. **口径实体化第 1 轮（2026-11-21 四，未提交）**：`area.admin_level`/`agency_level`、`source.excerpt_status` 落库并派生（`migrate_level_fields.py`），新增分析视图 `v_analysis_area`；validate 增枚举校验。agency_level 分布 city 437 / county 394 / province 378 / unknown 229 / town 37；excerpt_status 290 verbatim / 190 digest / 14 missing。下一轮：报告切换视图 + county_roster + evidence_debt

13. **口径实体化第 2 轮（2026-11-21 四晚）**：`county_roster`（15 县：matched 2 / not_area 13）与 `evidence_debt`（774 条）入主库；`report_ledgers.py` 出两份报告；层级分布改读 `agency_level` 字段（省378/地市437/县区394/乡镇37/未知228）；validate 增两张台账校验、issues=0。下一轮：`area_policy_map.evidence_tier` 回写 + 前端网站（web/）

14. **清欠账（2026-11-21 五）**：evidence_debt 774→560，其中**可执行仅 43**（digest 30 / missing 12）；no_primary 231→182、digest 190→30；主统计 591→630、宽 846；新增 4 个清账脚本（promote_sources_to_policies / fix_promoted_policies / clear_evidence_debt / reanchor_excerpts / refetch_missing_sources）；`evidence_debt` 增 `actionable` 列。下一轮：前端（web/）

15. **口径裁定（2026-11-21 五）**：对外总量改用 M 层 **1462**（area 1362 + belt 100，示范带计入）；删除长沙「集中连片」113 条（不是片区化，docs/01 §13）；主统计降为 P 层子口径 629。新增 `drop_area_batch.py`；`macro_unit` 补 belt 年份/归属/证据强度。公众号通道：搜狗线索可用、正文抓取被验证码+Browser Bridge 挡住，需用户装 OpenCLI 扩展

16. **公众号通道打通（2026-11-21 晚）**：OpenCLI 扩展装好后可抓公众号正文与长图；`wechat_fetch_urls.py`（URL→正文）、`wechat_ocr_images.py`（长图→OCR）、`wechat_batch_collect.py`（检索式批量）。首胜：山东第五批 102 个片区（新建70+提升32）从公众号长图 OCR 解析并入库 86 条待核，M 层 1462→1548。SOP 见 `reports/gaps/公众号采集通道-2026-11-21.md`
