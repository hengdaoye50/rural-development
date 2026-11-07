import json, sys
sys.stdout.reconfigure(encoding="utf-8")
p = r"D:\CODEX\全国乡村片区化数据库\data\stage\POL-ZJ03-policy.jsonl"
raw = open(p, "rb").read()
print("BOM:", raw[:3] == b"\xef\xbb\xbf")
print("bytes:", len(raw), "lines:", len(raw.splitlines()))
lines = raw.decode("utf-8").splitlines()
print("all parse:", all(json.loads(l) for l in lines))
r = json.loads(lines[26])
print("\n样本(title/url/doc_no/issuer):")
for k in ("title", "doc_no", "issuer", "issuer_level", "doc_type", "source_kind", "issued_ymd",
          "published_ymd", "credibility", "instruments", "target_areas", "budget_wan", "url"):
    print(f"  {k} = {r[k]}")
print("\nfull_text 前 300 字:")
print(r["full_text"][:300])
print("\nfull_text 末 200 字:")
print(r["full_text"][-200:])
print("\nareas:", r["areas"])
