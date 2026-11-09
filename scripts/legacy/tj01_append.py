"""One-off TJ01 helper: append record specs to POL-TJ01-policy.jsonl.

Not part of the pipeline. Each spec is a JSON file under $TEMP/tj01/spec.
Spec fields = the JSONL record fields. If "_text_file" is present, full_text is
read from that file; otherwise the "full_text" key is used as-is.

Usage:
  python tj01_append.py            # append all not-yet-appended specs
  python tj01_append.py --check    # validate only
"""
import io
import json
import os
import sys
import time

BATCH = os.path.join("data", "stage", "batches", "POL-TJ01-policy.jsonl")
SPEC_DIR = os.path.join(os.environ.get("TEMP", "."), "tj01", "spec")
TXT_DIR = os.path.join(os.environ.get("TEMP", "."), "tj01", "txt")

REQUIRED = [
    "slug", "url", "title", "doc_no", "issuer", "issuer_level", "issued_ymd",
    "published_ymd", "doc_type", "source_kind", "province_code", "city_code",
    "county_code", "instruments", "scope_desc", "target_areas", "budget_wan",
    "valid_state", "credibility", "summary", "areas", "events", "fetched_at",
    "full_text",
]
SK_OK = {"政策文件", "政府公报", "部门动态", "新闻发布"}


def load_existing():
    urls, keys = set(), set()
    if not os.path.exists(BATCH):
        return urls, keys
    with io.open(BATCH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            urls.add(o.get("url"))
            keys.add((o.get("doc_no") or "") + "|" + (o.get("issuer") or ""))
    return urls, keys


def build(path):
    with io.open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    tf = spec.pop("_text_file", None)
    if tf:
        with io.open(os.path.join(TXT_DIR, tf), encoding="utf-8") as fh:
            spec["full_text"] = fh.read().strip()
    missing = [k for k in REQUIRED if k not in spec]
    if missing:
        raise SystemExit(f"{os.path.basename(path)}: missing {missing}")
    if spec["source_kind"] not in SK_OK:
        raise SystemExit(f"{os.path.basename(path)}: bad source_kind {spec['source_kind']}")
    if spec["credibility"] not in ("A", "B"):
        raise SystemExit(f"{os.path.basename(path)}: bad credibility")
    if "gov.cn" not in spec["url"]:
        raise SystemExit(f"{os.path.basename(path)}: non-gov url {spec['url']}")
    if len(spec["full_text"]) < 150:
        raise SystemExit(f"{os.path.basename(path)}: full_text too short")
    return spec


def main():
    check_only = "--check" in sys.argv
    urls, keys = load_existing()
    added = 0
    for name in sorted(os.listdir(SPEC_DIR)):
        if not name.endswith(".json"):
            continue
        rec = build(os.path.join(SPEC_DIR, name))
        key = (rec.get("doc_no") or "") + "|" + (rec.get("issuer") or "")
        if rec["url"] in urls or (rec.get("doc_no") and key in keys):
            print(f"SKIP dup: {name}")
            continue
        orphans = [a["area_id"] for a in rec["areas"] if not a.get("area_id")]
        if orphans:
            raise SystemExit(f"{name}: empty area_id")
        print(f"OK  {name}: {rec['title'][:50]} chars={len(rec['full_text'])}")
        if check_only:
            continue
        with io.open(BATCH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        urls.add(rec["url"])
        keys.add(key)
        added += 1
    print(f"done, appended={added}")


if __name__ == "__main__":
    main()
