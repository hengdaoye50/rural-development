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
