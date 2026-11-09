"""一次性：按省份列出可能对应扫描件的政策标题，供人工判定原件归属。"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
conn = sqlite3.connect(ROOT / "data" / "db" / "片区库.sqlite3")
conn.row_factory = sqlite3.Row

WANT = {
    "210000": ("辽宁", ("辽农领办", "示范带", "十五五", "规划纲要")),
    "630000": ("青海", ("大财", "衔接", "资金", "和美乡村", "国土空间")),
    "360000": ("江西", ("大余", "四融一共")),
}

for prov, (name, kws) in WANT.items():
    print(f"===== {name} =====")
    for r in conn.execute(
        "SELECT policy_id, title, local_path, credibility FROM policy "
        "WHERE province_code = ?", (prov,)
    ):
        if any(k in r["title"] for k in kws):
            print(f"  {r['policy_id']} [{r['credibility']}] {r['title'][:64]}")
            print(f"      {r['local_path']}")
