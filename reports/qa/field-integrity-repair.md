# 字段完整性修复：错位与日期污染

日期：2026-11-24
脚本：`scripts/repair_misaligned_rows.py`
审计明细：`reports/qa/misaligned-rows.csv`（127 行，逐行保留修复前后值）

## 修了什么

### 缺陷一：`repair-2026-09` 批次的字段错位（51 行）

该批次把带逗号的 `tags` 值写成带引号单元格，却把紧随其后的
`town_codes` / `cover_desc` / `scale_villages` / `issuer` / `summary`
一并写进了同一个引号区域。结果是这些值整体落进 `tags` 列，
而 header 对应列位被 `repair-2026-09` 字面量和 `2024-01-01` 占位日期填满。

两种表现：

- **A 型（41 行，江苏 15 / 陕西 10 / 甘肃 8 / 宁夏 5 / 青海 3）**：
  `town_codes`、`cover_desc`、`scale_villages` 里是批次名或日期
- **B 型（10 行，浙江）**：结构化字段本身是空的，坏在 `tags` 被塞进了镇名与覆盖范围描述

修复前，全库有 32 行 `town_codes` 是字面量 `repair-2026-09`，
2 行 `cover_desc` 同；这些值会让任何按字段做的统计（镇域覆盖、片区规模）失真。

### 缺陷二：`summary` 被写成日期（76 行）

早期多个批次把 `founded_ymd` 的值漏进了 `summary`：JS-batch01 30 行、
SH-batch01 16 行、AH-batch01 13 行、LN-batch01 8 行，其余散在
JS-batch03 / SD-batch02 / ZJ-batch01 / YN-batch01 / repair-2026-09。
日期不是摘要，一律清空；原始值留在审计 CSV 里。

## 还原规则

合并串的列内顺序实测为：

```
[tags...] [town_codes] [cover_desc] [scale_villages] [issuer] [summary] [批次尾标]
```

`tags` 可能占多段，故先消费「不以镇/乡/街道结尾」的前导段作为 tags，
第一个以镇名结尾的段作 `town_codes`，其后第一个较长的中文描述作 `cover_desc`，
剩余段中第一个纯数字作 `scale_villages`，最长的一段作 `summary`。

`scale_towns` 与 `issuer` 的空槽数量各行不同、无法稳定定位，**一律置空，不猜**。

## 修的过程中踩的三个坑

1. **`cover_desc` 和 `founded_precision` 是 NOT NULL**。第一版把取不到的值清空，
   `build_db` 直接 IntegrityError。`cover_desc` 改为「取不到就保留原值」，
   `founded_precision` 按项目既有约定填 `unknown`（同 A650001–A650005）。
2. **镇名判据不能用「包含」**。「和美乡村」里有个「乡」，被判成镇名，
   导致 tags 被清空、后续内容整体错位一格。改为只看**结尾**。
3. **批次名不能当唯一判据**。各行合并串尾标不同（江苏 `JS-batch02-repair`、
   青海/宁夏 `Northwest-batch01`、浙江 `ZJ-gap-jh-tz`），只查 `repair-2026-09`
   会漏掉一半，必须靠中间结果复核才发现。

## 结果

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `town_codes` 含批次名 | 32 | 0 |
| `cover_desc` 含批次名 | 2 | 0 |
| `summary` 为日期 | 78 | 0 |

`validate_db.py` issues=0，`area` 仍为 1093 行。

## 未处理（刻意）

- **22 行 `founded_ymd` 仍是 `2024-01-01`**：这些行的 `created_by` 不是本缺陷批次，
  无法判断是占位值还是真实日期，不猜。
- **4 行 `tags` 有三段**（A330083/084/086/087）：那是合法的三段标签，不是缺陷。
- **A330083 的 `cover_desc` 是 `1`**：原值本就是坏的，合并串里没有可替代的描述，
  而该列 NOT NULL，只能留着。属已知残留。
