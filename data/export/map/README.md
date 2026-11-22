# 地图数据（data/export/map）

由 `python scripts/export_map_data.py` 生成。边界缓存于 `data/geo/`（阿里 DataV 行政区划），
无网时用缓存，`--no-fetch` 只出 CSV。

## 文件

| 文件 | 内容 |
|---|---|
| `preview.html` | 自包含单页（内联 GeoJSON，无外部依赖）：指标切换、悬停提示、点击看省详情 |
| `provinces.geojson` | 35 个省级要素（含港澳台与南海诸岛，均为 0 值），`properties` 带统计 |
| `cities.geojson` | 449 个市级要素（直辖市为区级要素，`is_municipality=true`，数值取市域统计） |
| `分省汇总.csv` | 34 行：省码、片区数、主统计、宽统计、待核、待核占比、有依据、覆盖县、belt、政策数 |
| `分市汇总.csv` | 449 行，与 `cities.geojson` 一一对应（含 0 值城市，便于 join） |
| `分县汇总.csv` | 607 行：有片区的县（县码、省码、片区数、主统计、待核） |

## 字段

| 字段 | 含义 |
|---|---|
| `code` / `name` | 行政区划码与名称（GB/T 2260） |
| `areas` | 在册片区数（active，含待核） |
| `main` | 主统计 A+B（2022+ 且有 primary/support） |
| `wide` | 宽统计 A+B+C |
| `pending` | 待核条数 |
| `pending_share` | 待核占比（%） |
| `strong` | 有 primary/support 的记录数 |
| `counties` | 覆盖县数（按 `area.county_code` 去重） |
| `has_areas` | 该单元是否有数据（0 值要素靠它区分「没采到」与「没有」） |

## 用法与注意

- QGIS：直接拖 `.geojson`，按 `areas` 或 `main` 做分级设色（graduated）。
- kepler.gl / Mapbox：`code` 为 6 位字符串，join 时注意保留前导零。
- **0 值不等于「当地没有片区」**：只代表库里没有收录（县覆盖 615/2 856）。
  对外发布必须同时标「覆盖率」，不能只给 0 值地图。
- 港澳台无边界、无数据，要素存在但值为 0。
- 直辖市（京/津/沪/渝）的区级要素统一套用市域统计，做省级以下分析时不要用它们的区值。

## 复现

```powershell
python scripts/export_map_data.py            # 用缓存边界
python scripts/export_map_data.py --fetch    # 刷新边界（约 35 次请求）
python scripts/export_map_data.py --no-fetch # 只出 CSV
python scripts/export_map_preview.py         # 生成 preview.html（需先有 provinces.geojson）
```
