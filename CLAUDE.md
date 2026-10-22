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
│   └── 04-行政区划代码表.md  # 省市县国标代码与别名
├── data/
│   ├── raw/                  # 原始来源：按省分目录，只追加不覆盖
│   │   └── {省代码-省名}/{YYYYMM}-{关键词或来源}/
│   ├── stage/                # 半结构化中间表（清洗过程用）
│   ├── clean/                # 入库前最终 CSV（字段对齐数据字典）
│   └── db/                   # SQLite 主库（片区库.sqlite3）
├── scripts/                  # 采集/清洗/校验/导出脚本（Python）
├── reports/                  # 统计报告、图表、专题分析
└── archive/                  # 废弃版本，按日期归档，不删
```

命名规则：
- 中文目录/文件名用于人类可读文档与报告
- 数据文件、脚本、表名一律英文 snake_case
- 原始证据路径必须可回溯：`data/raw/{省}/{日期}-{来源}/原文.md` + `meta.json`
- 禁止在 `data/clean` 与 `data/db` 中手改数据；一切修改走脚本或 `data/stage`

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

# 仅用 by_province 重建 clean master（勿直接手改 master）
# 见 scripts/merge_by_province.py；by_province 优先于 master
```

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
