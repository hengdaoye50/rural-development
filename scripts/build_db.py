"""从 data/clean/*.csv 幂等重建 SQLite 主库。"""
from __future__ import annotations

import csv
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DB_PATH = ROOT / "data" / "db" / "片区库.sqlite3"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS region (
    region_code TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    short_name  TEXT,
    level       TEXT NOT NULL CHECK (level IN ('province','city','county','town','village')),
    parent_code TEXT,
    aliases     TEXT
);

CREATE TABLE IF NOT EXISTS area (
    area_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    name_norm           TEXT NOT NULL,
    type_code           TEXT NOT NULL CHECK (type_code IN ('T01','T02','T03','T04','T05','T06','T07','T08')),
    type_primary_note   TEXT,
    tags                TEXT,
    province_code       TEXT NOT NULL,
    city_code           TEXT NOT NULL,
    county_code         TEXT NOT NULL,
    town_codes          TEXT,
    cover_desc          TEXT NOT NULL,
    scale_villages      INTEGER,
    scale_towns         INTEGER,
    founded_ymd         TEXT,
    founded_precision   TEXT NOT NULL CHECK (founded_precision IN ('day','month','year','unknown')),
    status              TEXT NOT NULL CHECK (status IN ('运行中','待核','已撤销','已更名','已完成')),
    setup_kind          TEXT,
    lead_org            TEXT,
    issuer              TEXT,
    summary             TEXT,
    parent_area_key     TEXT,
    first_source_id     TEXT,
    record_state        TEXT NOT NULL CHECK (record_state IN ('active','superseded','withdrawn')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    created_by          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source (
    source_id     TEXT PRIMARY KEY,
    -- area_id 可指向 area.area_id 或 belt.belt_id（多片区共用来源时只标主实体）
    area_id       TEXT NOT NULL,
    url           TEXT NOT NULL,
    title         TEXT NOT NULL,
    publisher     TEXT NOT NULL,
    published_ymd TEXT,
    excerpt       TEXT NOT NULL,
    fetched_at    TEXT NOT NULL,
    credibility   TEXT NOT NULL CHECK (credibility IN ('A','B','C','D','E')),
    local_path    TEXT,
    hash_sha256   TEXT
);

CREATE TABLE IF NOT EXISTS policy (
    policy_id       TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    doc_no          TEXT,
    issuer          TEXT NOT NULL,
    issuer_level    TEXT NOT NULL CHECK (issuer_level IN ('province','city','county','town','other')),
    issued_ymd      TEXT,
    published_ymd   TEXT,
    date_precision  TEXT NOT NULL CHECK (date_precision IN ('day','month','year','unknown')),
    -- doc_type 为开放词表：实际存在「新闻发布」「复函」等类型，预设枚举会逼失真归类
    doc_type        TEXT NOT NULL,
    source_kind     TEXT NOT NULL CHECK (source_kind IN ('政策文件','政府公报','部门动态','新闻发布')),
    province_code   TEXT NOT NULL,
    city_code       TEXT,
    county_code     TEXT,
    instruments     TEXT,
    scope_desc      TEXT,
    target_areas    INTEGER,
    budget_wan      REAL,
    -- valid_state 为开放词表：实践中存在「有效」「已失效（征求意见稿）」等真实状态，
    -- 预设枚举会逼采集者失真归类，故不做 CHECK
    valid_state     TEXT NOT NULL,
    url             TEXT NOT NULL,
    local_path      TEXT NOT NULL,
    hash_sha256     TEXT,
    full_text_chars INTEGER,
    summary         TEXT,
    credibility     TEXT NOT NULL CHECK (credibility IN ('A','B')),
    fetched_at      TEXT NOT NULL,
    record_state    TEXT NOT NULL CHECK (record_state IN ('active','superseded','withdrawn')),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    created_by      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event (
    event_id    TEXT PRIMARY KEY,
    area_id     TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'area' CHECK (entity_type IN ('area','belt')),
    -- event_type 为开放词表：地方事件形态多样（规划编制/立项/人大监督/推进会/入选案例…），
    -- 预设枚举会逼采集者把观察到的事实硬塞进几个格子，故不做 CHECK
    event_type  TEXT NOT NULL,
    ymd         TEXT,
    note        TEXT,
    source_id   TEXT,
    policy_id   TEXT REFERENCES policy(policy_id)
);

CREATE TABLE IF NOT EXISTS area_policy_map (
    area_id     TEXT NOT NULL,
    policy_id   TEXT NOT NULL REFERENCES policy(policy_id),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('area','belt')),
    rel         TEXT NOT NULL DEFAULT 'support' CHECK (rel IN ('primary','support','mention')),
    PRIMARY KEY (area_id, policy_id)
);

CREATE TABLE IF NOT EXISTS area_region_map (
    area_id     TEXT NOT NULL REFERENCES area(area_id),
    region_code TEXT NOT NULL REFERENCES region(region_code),
    role        TEXT NOT NULL CHECK (role IN ('county','town','village','core','planned')),
    is_core     INTEGER NOT NULL CHECK (is_core IN (0,1)),
    PRIMARY KEY (area_id, region_code, role)
);

CREATE TABLE IF NOT EXISTS unique_active_area (
    county_code TEXT NOT NULL,
    name_norm   TEXT NOT NULL,
    PRIMARY KEY (county_code, name_norm)
);
CREATE TABLE IF NOT EXISTS belt (
    belt_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    name_norm           TEXT NOT NULL,
    belt_type           TEXT NOT NULL CHECK (belt_type IN ('带','圈','廊','片','走廊','环','线','其他')),
    theme               TEXT,
    province_code       TEXT NOT NULL,
    city_code           TEXT NOT NULL,
    county_code         TEXT,
    cover_desc          TEXT NOT NULL,
    scale_villages      INTEGER,
    scale_towns         INTEGER,
    announced_ymd       TEXT,
    year_precision      TEXT NOT NULL CHECK (year_precision IN ('day','month','year','unknown')),
    issuer              TEXT,
    source_id           TEXT,
    summary             TEXT,
    institutional_note  TEXT,
    record_state        TEXT NOT NULL CHECK (record_state IN ('active','superseded','withdrawn')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    created_by          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS belt_region_map (
    belt_id     TEXT NOT NULL REFERENCES belt(belt_id),
    region_code TEXT NOT NULL REFERENCES region(region_code),
    role        TEXT NOT NULL CHECK (role IN ('county','town','village','spine','node')),
    is_core     INTEGER CHECK (is_core IN (0,1)),
    PRIMARY KEY (belt_id, region_code, role)
);

CREATE TABLE IF NOT EXISTS unique_active_belt (
    province_code TEXT NOT NULL,
    name_norm     TEXT NOT NULL,
    belt_type     TEXT NOT NULL,
    PRIMARY KEY (province_code, name_norm, belt_type)
);

CREATE TABLE IF NOT EXISTS area_source_map (
    area_id     TEXT NOT NULL,
    source_id   TEXT NOT NULL REFERENCES source(source_id),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('area','belt')),
    rel         TEXT NOT NULL DEFAULT 'support' CHECK (rel IN ('primary','support','mention')),
    PRIMARY KEY (area_id, source_id)
);

-- 省级名单台账：每省「省级层面有没有一份可逐条对账的片区名单」
-- 用途：报覆盖率时分母来源登记；status 只用封闭枚举（见 docs/02）
CREATE TABLE IF NOT EXISTS city_roster (
    city_code      TEXT PRIMARY KEY,
    city_name      TEXT,
    province_code  TEXT NOT NULL,
    roster_name    TEXT,
    roster_scope   TEXT,
    policy_id      TEXT,
    source_id      TEXT,
    official_count INTEGER,
    in_db_count    INTEGER,
    count_basis    TEXT,
    status         TEXT NOT NULL CHECK (status IN
                     ("matched","partial","count_only","not_area","none")),
    note           TEXT,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS province_roster (
    province_code  TEXT PRIMARY KEY,
    roster_name    TEXT,           -- 名单名称；空表示未见
    roster_scope   TEXT,           -- 批次/年度/文号
    policy_id      TEXT,           -- 库内 .gov.cn 全文（可空）
    source_id      TEXT,           -- 只有媒体来源时记 source（可空）
    official_count INTEGER,        -- 官方数/名单条数（空=未取得）
    in_db_count    INTEGER,        -- 人工核定的库内已入库条数（空=按关联现算）
    count_basis    TEXT,           -- 名单条数/年度目标/年度实际/累计/试点县数
    status         TEXT NOT NULL CHECK (status IN
                     ('matched','partial','count_only','not_area','none')),
    note           TEXT,
    updated_at     TEXT NOT NULL
);

-- 统计口径卡（docs/01 §10）：把「入库」与「进分母」分开。
-- A 窗口内+有依据 / B 2022 前成立但延续至今 / C 时间不详+有依据 / D 口径外 / E 无依据
-- D 组不删记录、不改 status，只在此处被排除，口径调整只改本视图
CREATE VIEW IF NOT EXISTS area_caliber AS
SELECT *,
       CASE
         WHEN time_bucket = 'pre2022_stale' THEN 'D'
         WHEN has_hard = 0                  THEN 'E'
         WHEN time_bucket = 'in_window'     THEN 'A'
         WHEN time_bucket = 'carried_over'  THEN 'B'
         ELSE 'C'
       END AS caliber_group,
       CASE WHEN status <> '待核' THEN 1 ELSE 0 END AS in_scope,
       CASE WHEN status <> '待核'
             AND has_hard = 1
             AND time_bucket IN ('in_window','carried_over') THEN 1 ELSE 0 END AS in_main_stat
FROM (
    SELECT a.area_id, a.name, a.province_code, a.county_code, a.status, a.setup_kind,
           a.founded_ymd, a.founded_precision,
           CASE WHEN EXISTS (SELECT 1 FROM area_policy_map m
                             WHERE m.area_id = a.area_id
                               AND m.rel IN ('primary','support'))
                THEN 1 ELSE 0 END AS has_hard,
           CASE
             WHEN a.founded_precision = 'unknown' OR COALESCE(a.founded_ymd,'') = '' THEN 'unknown'
             WHEN substr(a.founded_ymd,1,4) >= '2022' THEN 'in_window'
             WHEN EXISTS (SELECT 1 FROM area_policy_map m
                          JOIN policy p ON p.policy_id = m.policy_id
                          WHERE m.area_id = a.area_id
                            AND COALESCE(NULLIF(p.published_ymd,''), NULLIF(p.issued_ymd,''), '') >= '2023')
               OR EXISTS (SELECT 1 FROM event e
                          WHERE e.area_id = a.area_id AND COALESCE(e.ymd,'') >= '2023')
               THEN 'carried_over'
             ELSE 'pre2022_stale'
           END AS time_bucket
    FROM area a
    WHERE a.record_state = 'active'
);

-- 宏观层（docs/01 §11）：命名单元 = area + belt，去重后按省计数。
-- 只放宽证据强度（含待核/媒体来源/时间不详），对象类型仍受 docs/01 §3 约束。
-- belt 与 area 同省同名时保留 area 那条，避免同一单元被数两次。
CREATE VIEW IF NOT EXISTS macro_unit AS
SELECT a.area_id AS unit_id, 'area' AS kind, a.name, a.name_norm, a.province_code,
       a.county_code, a.status, a.type_code AS subtype, a.setup_kind,
       CASE WHEN a.status <> '待核' THEN 1 ELSE 0 END AS in_policy_layer,
       CASE WHEN EXISTS (SELECT 1 FROM area_policy_map m
                         WHERE m.area_id = a.area_id AND m.rel IN ('primary','support'))
            THEN 1 ELSE 0 END AS has_hard
FROM area a
WHERE a.record_state = 'active'
UNION ALL
SELECT b.belt_id, 'belt', b.name, b.name_norm, b.province_code,
       NULL, NULL, b.belt_type, NULL,
       0, 0
FROM belt b
WHERE b.record_state = 'active'
  AND NOT EXISTS (SELECT 1 FROM area a
                  WHERE a.record_state = 'active'
                    AND a.province_code = b.province_code
                    AND a.name_norm = b.name_norm);
"""

CSV_TABLES = {
    "region": "region.csv",
    "area": "area.csv",
    "source": "source.csv",
    "policy": "policy.csv",
    "event": "event.csv",
    "area_region_map": "area_region_map.csv",
    "belt": "belt.csv",
    "belt_region_map": "belt_region_map.csv",
    "area_source_map": "area_source_map.csv",
    "area_policy_map": "area_policy_map.csv",
    "province_roster": "province_roster.csv",
    "city_roster": "city_roster.csv",
}


def _rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        for table, fname in CSV_TABLES.items():
            rows = _rows(CLEAN / fname)
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ",".join("?" for _ in cols)
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            conn.executemany(sql, [tuple(r.get(c, "") or None for c in cols) for r in rows])

        # unique constraint on active areas
        for r in _rows(CLEAN / "area.csv"):
            if r.get("record_state") == "active":
                conn.execute(
                    "INSERT OR IGNORE INTO unique_active_area (county_code, name_norm) VALUES (?,?)",
                    (r["county_code"], r["name_norm"]),
                )
        for r in _rows(CLEAN / "belt.csv"):
            if r.get("record_state") == "active":
                conn.execute(
                    "INSERT OR IGNORE INTO unique_active_belt (province_code, name_norm, belt_type) VALUES (?,?,?)",
                    (r["province_code"], r["name_norm"], r["belt_type"]),
                )

        meta = {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "tables": {t: len(_rows(CLEAN / f)) for t, f in CSV_TABLES.items()},
        }
        conn.execute(
            "CREATE TABLE IF NOT EXISTS build_meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)"
        )
        conn.executemany(
            "INSERT INTO build_meta (k, v) VALUES (?,?)",
            [(k, str(v)) for k, v in meta.items()] + [("tables_json", str(meta["tables"]))],
        )
        conn.commit()
    finally:
        conn.close()

    print(f"OK: rebuilt {DB_PATH}")


if __name__ == "__main__":
    sys.exit(build())
