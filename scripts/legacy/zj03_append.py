import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

BATCH = "data/stage/batches/POL-ZJ03-policy.jsonl"
ORDER = [
    "title", "doc_no", "issuer", "issuer_level", "issued_ymd", "published_ymd",
    "doc_type", "source_kind", "province_code", "city_code", "county_code",
    "instruments", "scope_desc", "target_areas", "budget_wan", "valid_state",
    "credibility", "summary", "slug", "areas", "events", "url", "fetched_at",
    "full_text", "full_text_chars",
]
SOURCE_KINDS = {"政策文件", "政府公报", "部门动态", "新闻发布"}


def main(src):
    recs = json.load(io.open(src, encoding="utf-8"))
    if isinstance(recs, dict):
        recs = [recs]
    existing = set()
    for line in io.open(BATCH, encoding="utf-8"):
        line = line.strip()
        if line:
            existing.add(json.loads(line)["url"])
    out = []
    for r in recs:
        assert r["source_kind"] in SOURCE_KINDS, r["source_kind"]
        assert r["credibility"] in {"A", "B"}, r["credibility"]
        if r["url"] in existing:
            print("SKIP dup url:", r["url"])
            continue
        r["full_text_chars"] = len(r["full_text"])
        ordered = {k: r[k] for k in ORDER if k in r}
        missing = [k for k in ORDER if k not in ordered]
        assert not missing, missing
        out.append(json.dumps(ordered, ensure_ascii=False))
        existing.add(r["url"])
    if out:
        with io.open(BATCH, "a", encoding="utf-8", newline="\n") as f:
            for line in out:
                f.write(line + "\n")
    print("appended", len(out))
    print("total lines", sum(1 for _ in io.open(BATCH, encoding="utf-8")))


if __name__ == "__main__":
    main(sys.argv[1])
