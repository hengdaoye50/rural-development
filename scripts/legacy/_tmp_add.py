"""Temporary helper: append one policy record (spec JSON + full-text file) to the GD02 batch."""
import json
import sys
from pathlib import Path

BATCH = Path("data/stage/batches/POL-GD02-policy.jsonl")

DEFAULTS = {
    "doc_no": "",
    "issuer": "",
    "issuer_level": "",
    "issued_ymd": "",
    "published_ymd": "",
    "doc_type": "",
    "source_kind": "",
    "province_code": "440000",
    "city_code": "",
    "county_code": "",
    "instruments": "",
    "scope_desc": "",
    "target_areas": None,
    "budget_wan": "",
    "valid_state": "现行有效",
    "url": "",
    "credibility": "A",
    "summary": "",
    "slug": "",
    "fetched_at": "2026-11-08",
    "areas": [],
    "events": [],
}


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    ft_file = spec.pop("full_text_file")
    text = Path(ft_file).read_text(encoding="utf-8").strip()
    rec = dict(DEFAULTS)
    rec.update(spec)
    rec["full_text"] = text
    missing = [k for k in ("title", "issuer", "issuer_level", "doc_type",
                           "source_kind", "url", "credibility") if not rec.get(k)]
    if missing:
        raise SystemExit("missing required: " + ",".join(missing))
    if len(text) < 200:
        raise SystemExit("full_text too short: %d" % len(text))
    if not rec["url"].startswith("http"):
        raise SystemExit("bad url")
    line = json.dumps(rec, ensure_ascii=False)
    with BATCH.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
    total = len(BATCH.read_text(encoding="utf-8").strip().splitlines())
    print("appended | chars=%d | total_lines=%d | %s" % (len(text), total, rec["title"]))


if __name__ == "__main__":
    main()
