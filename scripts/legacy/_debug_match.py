import sys, io, csv
sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8")
import importlib.util
spec = importlib.util.spec_from_file_location("m", "scripts/match_area_roster.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

areas = m.load_areas(None)
pool = [a for a in areas if a["county_code"] == "330305"]
print("pool:", [(a["area_id"], a["name"]) for a in pool])
for aname in ["海霞片区", "东岙顶片区", "观音礁片区"]:
    print("---", aname, "norm=", repr(m.norm(aname)))
    for a in pool:
        print("   ", a["area_id"], a["name"], "norm=", repr(m.norm(a["name"])),
              "eq=", m.norm(a["name"]) == m.norm(aname), "ov=", round(m.overlap(a["name"], aname), 2))
