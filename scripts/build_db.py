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
    policy_id   TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    doc_no      TEXT,
    issuer      TEXT NOT NULL,
    issued_ymd  TEXT,
    url         TEXT,
    summary     TEXT
);

CREATE TABLE IF NOT EXISTS event (
    event_id   TEXT PRIMARY KEY,
    area_id    TEXT NOT NULL REFERENCES area(area_id),
    event_type TEXT NOT NULL CHECK (event_type IN ('设立','挂牌','更名','扩围','撤销','评估','表扬')),
    ymd        TEXT,
    note       TEXT,
    source_id  TEXT
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
