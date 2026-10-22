"""导出 clean 数据为 Excel，便于非技术协作方阅读。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "data" / "clean" / "全国乡村片区数据库-export.xlsx"

TABLES = ["area", "belt", "source", "region", "policy", "event", "area_region_map", "belt_region_map"]


def export() -> None:
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        for t in TABLES:
            p = CLEAN / f"{t}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
            # 防公式注入
            for col in df.columns:
                df[col] = df[col].map(lambda v: v if not str(v).startswith("=") else f"'{v}")
            df.to_excel(xw, sheet_name=t[:31], index=False)
    print(f"OK: {OUT}")


if __name__ == "__main__":
    sys.exit(export())
