"""核对逆向校验所需的 15 个辽宁县码是否与民政部国标一致。"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fr", ROOT / "scripts" / "fill_region_counties.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

counties = mod.parse_counties(mod.SRC.read_text(encoding="utf-8", errors="replace"))
idx = {name: (code, city) for code, name, city in counties}

WANT = ["于洪区", "新民市", "康平县", "海城市", "宽甸满族自治县", "凌海市",
        "大石桥市", "阜新蒙古族自治县", "细河区", "灯塔市", "弓长岭区",
        "铁岭县", "西丰县", "北票市", "龙城区", "兴城市"]
for w in WANT:
    code, city = idx.get(w, ("NOT FOUND", ""))
    print(f"  {w:<14} {code}  市={city}")

print(f"\n解析总计 {len(counties)} 条")
