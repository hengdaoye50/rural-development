# 全国乡村片区化数据库

统计全国各省市自治区下，**县/区以下**设立「片区」推动乡村振兴的实践，并建成可查询、可校验、可扩展的结构化数据库。

## 项目目标

1. 建立「片区」的操作性定义与分类体系（见 `docs/01-概念界定.md`）
2. 按统一数据字典采集全国县级以下片区实体及其政策来源（见 `docs/02-数据字典.md`）
3. 落地为 SQLite 主库 + CSV/Excel 导出，支持按省/市/县/类型/年份交叉查询
4. 输出可发表的统计报告与地图数据

## 目录约定（什么放哪）

```
全国乡村片区化数据库/
├── CLAUDE.md                 # 本文件：项目约束与约定（唯一权威）
├── README.md                 # 对外说明
├── docs/
│   ├── 00-整体规划.md        # 路线图、里程碑、风险
│   ├── 01-概念界定.md        # 「片区」纳入/排除标准、类型学
│   ├── 02-数据字典.md        # 字段、取值、编码规则
│   ├── 03-采集规范.md        # 检索关键词、来源优先级、质检
│   ├── 04-行政区划代码表.md  # 省市县国标代码与别名
│   ├── 07-政策层.md          # 政策文件/政务动态的权威门槛、检索入口、工具编码
│   └── 08-并行采集编排.md    # 多 agent 分片、采集契约、失败抢救
├── data/
│   ├── raw/                  # 原始证据，只追加不覆盖
│   │   └── {ABBR}/           # 仅 2 字母省码（ZJ/SD/JS…），禁止 6 位码或中文
│   │       └── {YYYYMMDD}-{slug}/{原文.md, 原件.pdf, meta.json}
│   ├── stage/                # 采集中间产物，**根目录不放文件**，只允许三层
│   │   ├── batches/          # POL-{shard}-policy.jsonl 待入库批次
│   │   ├── shards/           # {shard}-brief.md + {shard}-counties.csv
│   │   └── candidates/       # *-candidates.csv 候选清单
│   ├── clean/
│   │   ├── {table}.csv       # master，禁止手改
│   │   └── by_province/      # 文件名只能是 {ABBR}-{table}.csv
│   └── db/                   # SQLite 主库（片区库.sqlite3）
├── scripts/                  # 参与管线的脚本，平铺
│   └── legacy/               # 一次性批次脚本与调试脚本，不参与管线
├── reports/
│   ├── qa/                   # 校验与审计报告
│   ├── gaps/                 # 缺采县清单
│   ├── pilot/                # 分片采集小结
│   └── *.md                  # 统计报告、专题分析
└── archive/                  # 废弃版本，按日期归档，不删
    └── {YYYY-MM}/            # 按年月归档
```

命名规则：
- 中文目录/文件名用于人类可读文档与报告
- 数据文件、脚本、表名一律英文 snake_case
- 原始证据路径必须可回溯：`data/raw/{ABBR}/{日期}-{slug}/原文.md` + `meta.json`
- 禁止在 `data/clean` 与 `data/db` 中手改数据；一切修改走脚本或 `data/stage`

**结构红线**（2026-10 规整后确立）：

1. `data/raw/` 顶层只能是 2 字母省码。历史遗留的 `330000-浙江` 已合并入 `ZJ`，
   新增证据一律用 2 字母
2. `data/stage/` 根目录不得出现文件，必须落入 `batches/` `shards/` `candidates/`
3. `data/clean/by_province/` 文件名只能是 `{ABBR}-{table}.csv`。禁止 `-batch03` 之类后缀——
   `merge_by_province.py` 按 `*-{table}.csv` 匹配，带后缀的文件会被静默跳过
4. `scripts/legacy/` 里的脚本不参与管线，也不要再被文档引用；管线脚本保持平铺
5. 结构调整必须先改本节，再执行 `scripts/migrate_layout.py`

## 工作流程约定

1. **约束优先**：新增目录或改字段，先改本文件与 `docs/02-数据字典.md`，再改实践
2. **概念优先于采集**：未写入 `01-概念界定.md` 的边界案例，不入库，记入 `docs/01-概念界定.md` 的「待裁定」
3. **证据链完整**：每条片区记录必须至少一条来源（URL + 摘录 + 抓取日期）；无来源不得入 clean
4. **可复现**：清洗与入库必须由 `scripts/` 脚本完成；禁止直接改 sqlite 业务表
5. **验证闭环**：每次批量入库后跑 `scripts/validate_db.py`，报告写入 `reports/qa/`
6. **密钥不入库**：爬虫/API 密钥放 `.env`，`.env` 进 `.gitignore`，永不进 git

## 技术约定

| 项 | 选择 | 说明 |
|---|---|---|
| 主库 | SQLite（`data/db/片区库.sqlite3`） | 单文件、易备份、支持 SQL |
| 中间/交换 | CSV（UTF-8 with BOM） | 便于 Excel 打开；字段顺序=数据字典 |
| 脚本语言 | Python 3.11+ | 优先用 `MIMO_PYTHON` 或项目 venv |
| 依赖 | 精简：requests / beautifulsoup4 / pandas / openpyxl / ruff | 新增依赖先写进本表 |
| 行政区划 | GB/T 2260 六位码 | 省市县；乡镇另附本地码 |
| 时间格式 | ISO `YYYY-MM-DD` 或 `YYYY-MM` | 未知日期留空，不猜 |
| 文本 | 简体中文原文保留；字段名英文 | 不机翻来源正文 |

## 质量红线（绝对不做）

- 不得编造、推测、补全无法核验的片区名称、时间、覆盖村数
- 不得因「搜不到」就删记录——改为 `status=待核` 并保留线索
- 不得混用「示范县 / 示范镇 / 示范村」冒充「片区」
- 不得把未写入类型学的「示范带、示范圈、走廊」直接入库

## 验证命令

```powershell
# 环境
$env:MIMO_PYTHON

# 结构与字段校验
& $env:MIMO_PYTHON scripts/validate_db.py

# 从 clean CSV 重建库（幂等）
& $env:MIMO_PYTHON scripts/build_db.py

# 多 agent 并行采集后：按省文件合并进 clean 根 CSV
& $env:MIMO_PYTHON scripts/merge_by_province.py

# 导出 Excel
& $env:MIMO_PYTHON scripts/export_excel.py

# 试点省区划码
& $env:MIMO_PYTHON scripts/gen_region_pilot.py

# 字段错位修复（tags 逗号拆列 / 空字段被吞）
& $env:MIMO_PYTHON scripts/repair_alignment.py

# M2 质量回填
& $env:MIMO_PYTHON scripts/m2_backfill.py
& $env:MIMO_PYTHON scripts/infer_times_from_text.py
& $env:MIMO_PYTHON scripts/export_excerpt_snapshots.py

# 快照完整性补漏（断链检测 -> 补采 -> 补哈希）
& $env:MIMO_PYTHON scripts/probe_dead_sources.py --csv reports/qa/dead-source-probe.csv
& $env:MIMO_PYTHON scripts/repair_source_snapshots.py          # 可访问的重抓，死链清空 local_path
& $env:MIMO_PYTHON scripts/backfill_source_hash.py             # 补录缺失的 hash_sha256

# 健康度总览（进度 + 质量信号汇总，只读）
& $env:MIMO_PYTHON scripts/health_report.py                    # -> reports/qa/health-latest.md

# 采集成果总览（分省矩阵 / 文种 / 年份 / 话语分化 / 缺口，全部现查现算）
& $env:MIMO_PYTHON scripts/report_corpus_overview.py           # -> reports/采集成果总览.md

# 漏挂反查：正文点名了片区但 area_policy_map 没挂（ingest 只认 JSONL 的 areas 字段）
& $env:MIMO_PYTHON scripts/audit_missing_policy_links.py
& $env:MIMO_PYTHON scripts/audit_missing_policy_links.py --csv reports/qa/missing-policy-links.csv

# 链接真实性：挂上的 primary/support 在政策全文里到底有没有点名该片区
# 输出 点名 / 仅提县镇地名（弱依据）/ 完全无关 三档，写 reports/qa/link-veracity.csv
& $env:MIMO_PYTHON scripts/audit_link_veracity.py
& $env:MIMO_PYTHON scripts/audit_link_veracity.py --csv reports/qa/link-veracity.csv

# 按审计结论归位 rel：link-wrong 解除、link-weak 降 mention（幂等）
# 同时改 by_province 与 master——只删 by_province 的话 master 会被当「补缺」并回来
& $env:MIMO_PYTHON scripts/apply_link_veracity_fix.py --dry-run
& $env:MIMO_PYTHON scripts/apply_link_veracity_fix.py
# 跑完必须接：merge_by_province -> build_db -> validate_db -> health_report

# 无 primary/support 依据的在册片区清单（下一轮补采作业面）
& $env:MIMO_PYTHON scripts/list_thin_evidence_areas.py     # -> reports/qa/areas-thin-evidence.csv

# 类型边界审计：按「有无设立文件」对账 area(T03) 与 belt，只排序不判定
& $env:MIMO_PYTHON scripts/audit_type_boundary.py          # -> reports/qa/type-boundary-audit.csv

# 派生设立方式 setup_kind（roster 名单型 / deployment 部署型 / unknown）
# 依据 docs/01 §10.2；只写 by_province（area 是实体表，merge 会重建 master）
& $env:MIMO_PYTHON scripts/classify_setup_kind.py --dry-run
& $env:MIMO_PYTHON scripts/classify_setup_kind.py

# 宏观层 M（docs/01 §11）：各省命名单元数量，宽口径，只用于看量级与分布
& $env:MIMO_PYTHON scripts/report_macro_layer.py            # -> reports/宏观层-分省数量.md
# 视图 macro_unit 为唯一来源（area + belt 去跨表重名）

# 覆盖率缺口定位：把零单元县收敛成「手里已有证据」的一小撮，按 T1/T2/T3 分层
# 只定位不抽名——正文正则抽片区名七成是城市控规分区，别试
& $env:MIMO_PYTHON scripts/find_coverage_gaps.py            # -> reports/gaps/coverage-gaps.{md,csv}

# 数据清洗三件套（都幂等，先 --dry-run 看会改哪些行）
& $env:MIMO_PYTHON scripts/apply_area_fixes.py --dry-run    # 占位码/城市码/数值字段污染
& $env:MIMO_PYTHON scripts/fix_region_integrity.py --dry-run # region 补缺失市级行、退休码去重
& $env:MIMO_PYTHON scripts/repair_area_sources.py --dry-run  # first_source_id 悬空，按 raw 证据复原
# 清洗记录见 reports/qa/data-cleaning-2026-11.md

# 区划归属行补漏：active 片区缺 area_region_map 行（按 map 聚合会静默少算）
& $env:MIMO_PYTHON scripts/repair_area_region_map.py --dry-run
& $env:MIMO_PYTHON scripts/repair_area_region_map.py
# 跑完接 merge_by_province -> build_db -> validate_db；validate 已把缺行记为 issue

# 待核逐条裁定：按裁定表改 status/name/cover/rel（幂等；只写 by_province）
# 裁定表 data/stage/candidates/pending-decisions-{date}.csv，列见脚本 docstring
& $env:MIMO_PYTHON scripts/adjudicate_pending_areas.py --dry-run
& $env:MIMO_PYTHON scripts/adjudicate_pending_areas.py
# 跑完同样接 merge_by_province -> build_db -> validate_db -> health_report

# region 补省/市级行：县级 parent_code 引用了 region 里不存在的市码时用
# 数据源是仓库内民政部《县以上行政区划代码》HTML；只补省/市两级，不动县级分母
& $env:MIMO_PYTHON scripts/backfill_region_from_mca.py --dry-run
& $env:MIMO_PYTHON scripts/backfill_region_from_mca.py
# 跑完接 build_db -> validate_db

# 文档口径守卫（只读）：README/docs/00/docs/01/docs/09/HANDOVER 的关键数字与库内值比对
& $env:MIMO_PYTHON scripts/check_doc_caliber.py
# 不一致即非零退出；每次批量入库后跑一次，防止「数字地基」再次漂移

# 公众号线索（只做「发现」，不做「证据」；公众号不是 .gov.cn，不得进 policy）
& $env:MIMO_PYTHON scripts/wechat_leads.py "潍坊 片区 乡村振兴" "昌邑 片区 乡村振兴"
& $env:MIMO_PYTHON scripts/wechat_resolve.py "<搜狗 link>"   # 当前被反爬拦截，仅用于探测
# 产出 reports/gaps/wechat-leads-{date}.csv；说明见 reports/gaps/wechat-leads-2026-11.md

# 批量媒体/融媒线索（按缺口清单逐县跑；搜狗约 50-60 次请求触发反爬，自动冷却/中止）
& $env:MIMO_PYTHON scripts/media_leads.py --from-code 0 --limit 50 --channels sogou-wechat
# 产出 data/stage/candidates/media-leads-{date}.csv；实测与方案见 reports/gaps/media-leads-2026-11.md

# 公众号正文（需 OpenCLI Browser Bridge：Chrome 运行中 + 扩展已连）
# 必须一条龙跑：mp.weixin 的签名链一次性，复用旧链只会拿到空壳
& $env:MIMO_PYTHON scripts/wechat_fetch.py --query "沁水县 片区 乡村振兴" --top 4
# 产出 data/stage/candidates/wechat-md/*.md + wechat-fetch-{date}.csv
# 说明见 reports/gaps/wechat-article-fetch-2026-11.md

# 抓 .gov.cn 原文 -> 直接生成 ingest_policy 批次（正文自动提取，过短即拒绝）
& $env:MIMO_PYTHON scripts/fetch_gov_doc.py --out data/stage/batches/POL-{省码}-{名}-policy.jsonl `
    --doc "url=https://...,title=...,issuer=...,issuer_level=province,published_ymd=2025-12-31,province_code=370000"
# 非 .gov.cn 域名直接拒绝；"正文 < 150 汉字"也拒绝，不生成残缺记录

# 统计口径（docs/01 §10）：唯一来源是视图 area_caliber，别自己写口径 SQL
#   select count(*) from area_caliber where in_main_stat=1;              -- 主统计 A+B
#   select caliber_group, count(*) from area_caliber where in_scope=1 group by 1;

# 名单比对：把一份官方名单 CSV 与库内片区做集合匹配（按县限定，防跨县假阳性）
# 名单 CSV 列：county, area_name, key_village, source_url, note
& $env:MIMO_PYTHON scripts/match_area_roster.py data/stage/candidates/roster-{省码}-{批次}.csv
& $env:MIMO_PYTHON scripts/match_area_roster.py <roster.csv> --status 待核 --out reports/qa/roster-match.csv

# 仅用 by_province 重建 clean master（勿直接手改 master）
# 见 scripts/merge_by_province.py；by_province 优先于 master
```

### 扫描件 OCR 补采

「PDF 是图片、pypdf 抽 0 字符」的来源用这条补。**必须用 `.venv-ocr` 环境跑**，
不能用 `MIMO_PYTHON`（后者没有 OCR 依赖，也不要往里装）：

```powershell
# 一次性的 OCR 环境（rapidocr-onnxruntime + onnxruntime + pypdfium2），已 .gitignore
uv venv .venv-ocr --python 3.12
uv pip install --python .venv-ocr\Scripts\python.exe rapidocr-onnxruntime pypdfium2

# 本地 PDF -> 原文.md（缺省写到 PDF 同目录）
& ".venv-ocr\Scripts\python.exe" scripts/ocr_pdf.py path\to\原件.pdf
# 直接给 URL：下载后识别
& ".venv-ocr\Scripts\python.exe" scripts/ocr_pdf.py https://xx.gov.cn/a.pdf --out data\raw\JX\xxx\原文.md
# 先看效果不写盘 / 只跑某几页 / 小字模糊时提高倍率
& ".venv-ocr\Scripts\python.exe" scripts/ocr_pdf.py 原件.pdf --pages 1-3 --dry-run
& ".venv-ocr\Scripts\python.exe" scripts/ocr_pdf.py 原件.pdf --scale 3.0
```

**OCR 不是无损的**：实测会把「〔2024〕」认成全角括号、把「五好两宜」偶尔认成「五好两宣」。
`ocr_pdf.py` 默认调用纠错层（`scripts/ocr_normalize.py`）处理这两类错误：文号括号按模式归一，
专名用库内片区名/市县名做「只差一个形近字」的定向替换。`--no-fix` 可关掉。
纠错两件套也可单独跑在已有文件上：

```powershell
& $env:MIMO_PYTHON scripts/ocr_normalize.py --check 原文.md   # 只报告会改什么
& $env:MIMO_PYTHON scripts/ocr_normalize.py --apply 原文.md   # 就地改写（幂等）
```

纠错前后都要抽样校读：规则只兜住已知模式，认不出的错字仍需人工。`hash_sha256` 按最终写入的字节算。

### 政策层（`policy` / `area_policy_map` / `event`）

```powershell
# 表头升级到 v0.2 政策层结构（幂等；schema 变更后先跑这个）
& $env:MIMO_PYTHON scripts/migrate_policy_schema.py

# 从现有 source 筛出政策文件候选，输出 data/stage/candidates/policy-candidates.csv
& $env:MIMO_PYTHON scripts/policy_backfill_candidates.py

# 政策批次入库：stage JSONL -> raw 全文存档 + by_province CSV
& $env:MIMO_PYTHON scripts/ingest_policy.py data/stage/batches/POL-{省码}-{序号}-policy.jsonl
& $env:MIMO_PYTHON scripts/ingest_policy.py --dry-run data/stage/batches/xxx.jsonl   # 先看解析结果
& $env:MIMO_PYTHON scripts/ingest_policy.py --purge POL-{省码}-{序号}-policy  # 回滚该批次

# 补录漏挂的片区↔政策映射（采集端 areas 漏项；url 去重会整条跳过，只能定点补）
& $env:MIMO_PYTHON scripts/add_area_policy_link.py A120007 P120001 primary "市级方案点名该片区"
& $env:MIMO_PYTHON scripts/add_area_policy_link.py --dry-run A210009 P210001 primary "省级名单含该示范带"

# 剔除口径不符的误录（raw 存档移到 archive/，不删）
& $env:MIMO_PYTHON scripts/drop_policy.py P540013 "中央全会规划建议，非县区级片区化部署"

# 并行采集：生成分片清单（每个分片一份 brief.md + counties.csv）
& $env:MIMO_PYTHON scripts/gen_policy_shards.py
& $env:MIMO_PYTHON scripts/gen_policy_shards.py ZJ01 SD01   # 只生成指定分片

# 编码一致性审计：查「声称有某政策工具但全文找不到依据」的记录
& $env:MIMO_PYTHON scripts/audit_instruments.py
& $env:MIMO_PYTHON scripts/audit_instruments.py --batch POL-ZJ01-policy --csv reports/qa/instruments-audit.csv
```

**并行采集契约**（详见 `docs/08-并行采集编排.md`）：子智能体只写 `data/stage/batches/POL-{shard}-policy.jsonl`，
不写 `data/clean`、不分配 ID；`ingest_policy.py` 串行编号并去重（同一 url 或 `doc_no+issuer` 自动跳过）。

**政策层硬约束**（详见 `docs/07-政策层.md`）：

- 只收 `.gov.cn` 域名原文或政府公报；商业门户/聚合站/自媒体**禁止入 `policy`**
- `credibility` 只允许 `A`/`B`
- 必须存**全文**（`local_path` 指向 `原文.md`，`full_text_chars` 可复核），只存摘录的退回重采
- `hash_sha256` 按磁盘字节计算，写入固定 LF，保证 `sha256(file) == hash_sha256` 可验证
- 采集以「县 × 政策链条」为单位，不按「片区 × 一段话」

**并发约定**：多 agent/多人采集时，clean 行先写入 `data/clean/by_province/{JS|ZJ|SD|...}-*.csv`，再 `merge_by_province.py`，禁止直接改 `data/clean/*.csv`。

**来源关联约定**：一条来源可支撑多个片区（`source.area_id` 记主实体，其余片区用 `area.first_source_id` 指向该 source）。belt 来源的 `source.area_id` 填 `belt_id`。

新增脚本时，在此节补充对应命令。

## 统计范围（已裁定）

- **时间**：重点 **2022 年前后至今**。地方「乡村片区化」提法约自 2022 年出现；中央层面表述见二十届四中全会与「十五五」规划建议中的片区化推进乡村振兴。此前记录仅当明确延续至今或转入振兴框架
- **地域**：大陆 31 个省级单位。**港澳台不纳入**
- **试点**：江苏、浙江、山东（口径尽量细）
- **象征性单元**：「示范带 / 示范圈 / 走廊 / 示范片」等**未实体化设立**的命名单元，**单独入 `belt` 表**，尽量统计，供后期分析；有实体机制的仍入 `area`（T03）

## 决策日志（Architecture decisions）

> 以下是**按时间记录的决策**，条目里的数字是**当时的快照**，不是当前值。
> 当前口径数字一律以 `docs/01` §10–§11 与 `reports/qa/health-latest.md` 为准；
> 引用历史数字时必须同时标注口径与快照日。

- 2025-06：主库选 SQLite 而非 Excel 长表——字段将超 20 列且需多表关联与 SQL 聚合
- 2025-06：「片区」采用**证据制准入**（官方来源可核验）而非名称包含「片区」二字即可入库
- 2025-06：原始证据与结构化数据严格分层（raw / stage / clean / db），保证可追溯与可重建
- 2025-06：象征性「示范带/圈/廊」与实体片区分表（`belt` vs `area`），避免污染片区统计
- 2025-06：试点定苏、浙、鲁；港澳台出库；时间锚点 2022
- 2026-09：江苏首批省级片区口径为 **39 个**（2024 指导意见），「40」是 2025 年底建成报道数，统计须区分
- 2026-09：`area_source_map` 支持一文多片区；`rel` 取 primary/support/mention
- 2026-10：**政策层独立成层**。`policy` 由 7 字段扩为 29 字段（含 `issuer_level`/`doc_type`/`instruments`/`budget_wan`/`full_text_chars`），新增 `area_policy_map`，`event` 加 `entity_type`/`policy_id`
- 2026-10：`policy` 引入**来源白名单制**——非 `.gov.cn` 一律不得入库。原 `source` 允许媒体转述，政策层不允许，因工具编码必须建立在原文上
- 2026-10：采集单位从「片区」改为「县 × 政策链条」。一份省级名单可覆盖上百片区，按县采边际成本远低于按片区采
- 2026-10：存档要求从「摘录 ≥40 字」升级为「全文 + 可复核哈希」。`full_text_chars < 150` 且非动态类触发 QA 警告
- 2026-10：**政策层进入探索性穷尽采集阶段，撤回编码收缩**。`instruments` 降级为描述性标签、
  不设数量上限、不做跨地区归一、不设金标准——用预设九类去统一会抹平北京「百千工程」、
  上海「五好两宜」、浙江「片区组团」等地区制度差异，而差异本身是研究对象。
  地方特有提法照原文记录；采集阶段只审「全 `.gov.cn` + 有全文 + 无编造」，不审编码
- 2026-10：**封闭枚举 vs 开放词表的分界**。仅结构性字段（`entity_type`/`rel`/`issuer_level`/
  `source_kind`/`credibility`/`type_code`/`precision`/`record_state`）用封闭枚举；
  描述观察的字段（`instruments`/`event_type`/`valid_state`/`doc_type`）一律开放词表，不做 CHECK。
  并行采集连续撞了三次枚举墙（片区组团/规划编制/已失效征求意见稿），每次都是逼采集者失真归类。
  新增取值不改 schema，校验只警告不拦截
- 2026-10：**快照完整性以「断链 0」为准**。`source` 的 128 条断链已补采 113 条、
  15 条死链（404/403/502）清空 `local_path` 并标记无快照——宁可显式缺，不留虚假存档。
  441 条快照全部记录 `hash_sha256`。新增脚本 `probe_dead_sources` / `repair_source_snapshots` /
  `backfill_source_hash`
- 2026-11：**江苏省级片区口径更正为 40 个**（原记 39 个）。省人大公报、省政府发布会、
  省农业农村厅材料均称「40 个宜居宜业和美乡村培育片区」；「39」只见于《群众》杂志
  省农业农村厅调研组文章，属口径偏差。**做覆盖率分母时用 40。**
- 2026-11：**抽样框改为「省级名单」，并承认它有适用边界**。此前采集以「政府网站可采性」
  为抽样框，属便利抽样，漏采率不可计算；辽宁的缺口（省名单 21 县、库内只 7 县）因此藏了两轮。
  改为「省名单 → 库内」逐条对账后（`scripts/check_roster_coverage.py`），漏采率可测。
  **但江苏等省并不整体公开省级片区名单**——江苏作为数据最厚的试点省，40 个省级片区的
  逐条明细只能从各市县材料拼（已拼出 8 条 + 零散数条）。故此法不是万能的：
  名单公开的省可算漏采率，名单不公开的省只能登记「不可对账」，不得用声明数字充分母
- 2026-11：**「有政策依据」只认 `primary`/`support`，`mention` 不计入。**
  此前 96.8% 是在「挂了链接即算」的意义上成立的，严格到「正文点名该片区」后为 **73.0%
  （623/854）**，县 74.3%。历史数字（65%／74.8%／80.8%／96.8%）一律标注为旧口径，
  不可与新口径混用。低点名率省（湖北 9%、贵州 16%、河南 26%、天津 33%）的根因是
  **依据类型不对**（品牌名来自报道、官方文本只写镇级片区；贵州挂在通用导则上），
  加采不解决，只能改名对齐官方表述或换抽样框
- 2026-11：**贵州改采《省级集成示范试点名单》作抽样框**。导则证明制度存在，
  不能证明某个片区存在，用它挂片区是把依据类型搞错
- 2026-11：**任何「删除」必须同时处理合并与入库两条回填路径**。`merge_by_province`
  对 map 表是「by_province 优先 + master 补缺」，只删 by_province 会被 master 补缺并回；
  `ingest_policy --purge` 只清库不清批次 JSONL，重跑就把已剔除的行灌回来。
  `add_area_policy_link --remove` 与 `apply_link_veracity_fix` 均已改为两处同删
- 2026-11：**「能入库」与「进分母」分成两件事**（`docs/01` §10 统计口径卡）。
  库里可以放宽（有线索即留档），统计必须收紧。落地为视图 `area_caliber`，五组互斥：
  A 窗内 434 / B 延续至今 12 / C 时间不详 172 / D 口径外 18 / E 无依据 218，合计 854。
  对外只报三个数之一：**主统计 A+B=446**、宽统计 A+B+C=618、全量库 854（仅描述采集规模）
- 2026-11：**「延续至今」用可查证代理判据**，不再停留在原则表述。2022 年前成立者，
  2023-01-01 后仍有 primary/support 政策或 event 即判延续，否则判口径外（D 组）
- 2026-11：**口径变更不改数据，只改视图与文档**。D 组不删记录、不改 `status`，
  由视图排除；这样任何口径调整都可逆，也不会污染 `data/raw` 证据链
- 2026-11：**`area`/`belt` 分界按「有无设立动作」，且设立动作分两种形态**。
  只认名单/批复/挂牌会把县域最普遍的设立方式判成不存在，故 2026-11 放宽：
  `roster`（名单/批复/公布/认定）与 `deployment`（政府工作报告、专项规划点名部署）
  都算设立，但**必须分列记录**（字段 `area.setup_kind`，派生脚本 `classify_setup_kind.py`）。
  实测差异是真实的制度差异：山东主统计里 34 条部署型 vs 4 条名单型，河北 20 条名单型 vs 0；
  合并成一个数字就会把它抹掉
- 2026-11：**统计分两层，各服务一种问题，不共用分母**（`docs/01` §11）。
  **M 宏观层**=命名单元（area+belt 去重）**1182**，宽在**证据强度**（媒体稿/待核/时间不详都收），
  但**对象类型一条不放宽**（示范县镇村、纯园区景区、城市控规分区仍不收），只用于看量级与分布；
  **P 政策层**=主统计 **446**，时间窗+`primary`/`support`+`setup_kind` 分列，政策分析只能用这个。
  **跨层相减没有意义**：M−P 的差不是「质量差的片区」，是「证据不足但确实被这么叫的单元」。
  M 层数字必须与「县覆盖率」并列报，单独出现即误导（青海 3 个只代表我们只采到 3 个）
- 2026-11：**CSV 里出现 schema 没有的列，必须报出来而不是静默丢**。
  `area_region_map.is_core` 在字典与 CSV 里都存在、DDL 里漏了 `belt_region_map.is_core`，
  于是 `merge_by_province` 按 master 旧表头写文件、把 by_province 的新列整个吞掉。
  已改为表头取并集 + DDL 补齐。**新增列时三处都要改：`docs/02`、DDL、by_province CSV**
- 2026-11：**公众号只能做「发现」，不能做「证据」**。`docs/07` 白名单只收 `.gov.cn`，
  公众号无论运营方是县农业农村局还是媒体，都不得进 `policy`；进 `source` 也只能支撑
  待核或 mention。正确顺序是「公众号确认叫什么 → 去 `.gov.cn` 找文本 → 再建档」，
  反过来做就是把媒体名当官方名。工具与产出见 `reports/gaps/wechat-leads-2026-11.md`
- 2026-11：**覆盖率提升的瓶颈是入口，不是算法**（`reports/gaps/coverage-gaps.md`）。
  三个负结果已实测：①全库正文正则抽片区名不可用（87 个候选七成是城市控规分区）；
  ②标题正则精度高但只出 7 条；③分母换成非市辖区无益（市辖区 19.8% > 非市辖区 17.3%）。
  故办法是「先定位文件、再逐份精读」：2344 个零单元县里收敛出 135 个手里有证据的
  （T1 本级文件 24 / T2 名单规划类 69 / T3 仅动态提及 42），并优先读**一篇覆盖多县**的
  高杠杆文件（河北 P130001 一次命中 17 县）
- 2026-11：**「零单元县」里有伪缺口，先做区划归属体检**。四川安州区 4 条片区挂在
  `510724`（region 占位码，名称等于代码），于是 `510705` 被算成「零单元」。
  修正后一进一出，**县覆盖数净变化为零**——这说明补采前必须先查区划归属，
  否则补了也白补。占位码清单见 `docs/00` §12 与 `reports/qa/` 相关报告
- 2026-11：**派生字段的判据不能用宽泛词**。`setup_kind` 初版把裸「公布」当名单信号，
  46 条「规划批后公布」被误判成名单型（浙江 100/112 → 70/142）。
  收词要挑长搭配（公布名单／公布第X批／结果公布）。**新判据先跑一遍再看分布变化**，
  突变就是误伤
- 2026-11：**数值字段会被非数值污染，且极隐蔽**。`scale_villages` 里发现过
  国道编号（G344→344）、省道编号（S611→611）、户数（800余户）、地名（盐城市/盐都区）
  和区间（3-5）。已清 12 条并在 `validate_db` 加「数值字段须为整数」检查。
  填数只填确定值，不用区间或概数糊过去
- 2026-11：**占位区划码会让聚合静默出错**。12 个 `name == region_code` 的占位行曾挂 19 个片区；
  另有 14 个市码（河北 6、辽宁 8）在 region 里根本不存在，26 条片区的 city_code 悬空。
  前者按片区自身 cover_desc 定县，后者按「该市码下辖县级行」印证后按 GB/T 2260 补名。
  `validate_db` 已加占位码与悬空城市码检查
- 2026-11：**同一实体要有「归属行」与「报数口径」双保险**。浙江 13 条 active 片区缺
  `area_region_map` 行，按 map 聚合的县覆盖静默少算、按 `area.county_code` 聚合又数得到，
  于是同库出现多套县覆盖数字（534／464／459）。已加 `repair_area_region_map.py` 与
  validate 硬检查；**县覆盖口径仍需单独裁定**，见 `reports/qa/接手审校-2026-11-18.md` §三 A
- 2026-11：**报告脚本里的数字不许硬编码**。`health_report.py` 曾把「全量库」写死 854，
  数据涨到 886 后报告照印旧值。所有口径数字必须从库现查；文档数字随快照重算（三处：`docs/01`、
  `README`、`docs/09`）
- 2026-11：**待核的「卡点」要逐条记，不能归成一个原因**。227 条待核里只有 174 条是
  「唯一来源为媒体」，另 53 条卡在名称未证实/规模待补/无具名实体。所以「补 .gov.cn 来源」
  只能解决子集（实测 2 条），把待核当单一原因会导致升级计划落空
- 2026-11：**待核裁定要「先读原文改名，再升级」**。16 条裁定里 3 条的核心问题是**名字不对**
  而不是证据不足：`吴中片区` 官方名是「东太湖宜居宜业和美乡村片区」、`湖埠片区` 实为
  「双浦环铜鉴湖·生态旅居片区组团」、「金山银海片区」官方全称含「和美金城」。
  只补来源不改名，等于把自拟名永久写进库。裁定表与落地脚本见
  `data/stage/candidates/pending-decisions-2026-11-18.csv` / `scripts/adjudicate_pending_areas.py`
- 2026-11：**`excerpt` 必须能在 `local_path` 快照里逐字找到**。裁定中发现 S044 的 excerpt
  含「安吉县大余村片区」，但其 744 字快照里没有该串——摘录与快照不一致，属证据链缺陷。
  入库时应校验 `excerpt in 快照正文`，不一致就报出来（待加检查）
- 2026-11：**「有证据在手」的县要看命中位置，不能只看命中**。T2 的 49 个县里，41 个是
  假阳性：安州规划顺带点到罗江/涪城/游仙（区位段）、绵阳政府网底栏挂盐亭/梓潼链接、
  云南「百千万」名单是示范乡镇村、武汉方案只写「示范片带」无专名。**关闭台账**
  `data/stage/candidates/gap-checks-*.csv` 记录 verdict，`find_coverage_gaps.py` 据此跳过，
  避免下一轮重复读同一批文件
- 2026-11：**区域表要按「父码闭包」校验，而不是只校验业务表引用**。`region` 早期从已有
  片区反推，导致 133 个地级市码根本不存在（县级行的 `parent_code` 悬空），而 `validate_db`
  只查 `area.city_code`，看不见 region 自身断裂。已用民政部代码表补省/市两级
  （`backfill_region_from_mca.py`，3 096→3 229 行）。**只补两级不补县级**：补县级会动
  「县级单位 2 856」分母，属需单独裁定的口径变更
- 2026-11：**文档口径要能「断言」，不能靠手抄**。一天内口径漂了三轮，
  `docs/01`（数字地基）连续两轮落后于库。新增 `scripts/check_doc_caliber.py`：
  把 README/docs/00/docs/01/docs/09/HANDOVER 里的关键数字与库内实测值比对，不一致即非零退出。
  **入库后固定动作**：`validate_db` → `health_report` → `check_doc_caliber`
- 2026-11：**跨县单元按 R10 分建，`parent_area_key` 首次落地**。辽宁「阜蒙县、细河区」
  示范带、江苏「亭湖+射阳」新洋港片区都只建了一个县的记录。已按 R10 两县分建并共享
  `parent_area_key`（`ingest_area_roster.py` 支持该列，`adjudicate_pending_areas.py` 可补写）。
  同一份省级名单里已有 2 条、缺 6 条的广西田园综合体也按「名单闭环」补齐 5 条
