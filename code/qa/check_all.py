#!/usr/bin/env python3
"""QA build gates for the Signature AI to Robot Matcher. Exit 1 on ANY failure.
Run: python3 code/qa/check_all.py
"""
import gzip
import hashlib
import json
import os
import re
import sys
import glob
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAIL = []
n_checks = [0]


def check(name, cond, detail=""):
    n_checks[0] += 1


def check(name, cond, detail=""):
    n_checks[0] += 1
    print(("PASS " if cond else "FAIL ") + name + (" — " + detail if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    state = json.load(open(os.path.join(ROOT, "data/state.json")))
    manifest = json.load(open(os.path.join(ROOT, "matcher-manifest.json")))
    pool = json.load(open(os.path.join(ROOT, "data/ai_pool.json")))
    bodies = json.load(open(os.path.join(ROOT, "data/bodies.json")))
    idx = json.load(gzip.open(os.path.join(ROOT, "data/index/pairs.idx.json.gz"), "rt"))
    api = json.load(open(os.path.join(ROOT, "api.json")))

    total = state["next_index"] - 1

    # 1. count agreement across every source
    check("manifest.total_pairs == state", manifest["total_pairs"] == total, "%s vs %s" % (manifest["total_pairs"], total))
    check("index rows == state", len(idx) == total, "%d vs %d" % (len(idx), total))
    chunk_n = sum(1 for _ in open(os.devnull))  # placeholder
    recs = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data/pairs/*.jsonl.gz"))):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if line.strip():
                    recs += 1
    check("chunk records == state", recs == total, "%d vs %d" % (recs, total))
    check("manifest.total_ais == pool", manifest["total_ais"] == len(pool))
    check("manifest.total_bodies == bodies", manifest["total_robot_bodies"] == len(bodies))
    check("api.json fresh", api["pairs_seeded"] == total and api["ai_count"] == len(pool) and api["bodies"] == len(bodies),
          str({k: api.get(k) for k in ("pairs_seeded", "ai_count", "bodies")}))

    # 2. pair id uniqueness + contiguity
    ids = [r[0] for r in idx]
    check("pair ids unique", len(set(ids)) == len(ids))
    nums = sorted(int(i.rsplit("-", 1)[1]) for i in ids)
    check("pair ids contiguous 1..N", nums == list(range(1, total + 1)))
    check("latest_pair_id correct", manifest["latest_pair_id"] == "JAH-PAIR-%06d" % total)

    # 3. orphan detection: every pair resolves to a real AI + a real ROBOT body
    body_ids = {b["id"] for b in bodies}
    ai_ids = {a["id"] for a in pool}
    bad_body = bad_ai = 0
    bad_score = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data/pairs/*.jsonl.gz"))):
        with gzip.open(f, "rt") as fh:
            for line in fh:
                if not line.strip():
                    continue
                p = json.loads(line)
                if p["body_id"] not in body_ids:
                    bad_body += 1
                if p["ai_id"] not in ai_ids:
                    bad_ai += 1
                if not (0 <= p["score"] <= 100):
                    bad_score += 1
                if not p["body_id"].startswith("JAH-BOT-"):
                    bad_body += 1  # robot side must ALWAYS be a robot body
    check("no orphan body refs", bad_body == 0, "%d bad" % bad_body)
    check("no orphan ai refs", bad_ai == 0, "%d bad" % bad_ai)
    check("scores in 0..100", bad_score == 0, "%d bad" % bad_score)

    # 4. body/ai id uniqueness
    check("body ids unique", len(body_ids) == len(bodies))
    check("ai ids unique", len(ai_ids) == len(pool))

    # 5. index hash matches manifest
    check("index hash matches", manifest["index_hash"] == sha256_file(os.path.join(ROOT, "data/index/pairs.idx.json.gz")))

    # 6. content-hash spot checks (first/middle/last body + ai)
    def canon_hash(rec):
        r = dict(rec); r.pop("content_hash", None)
        return hashlib.sha256(json.dumps(r, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for sample in (bodies[0], bodies[60], bodies[-1]):
        check("body hash %s" % sample["id"], sample.get("content_hash") == canon_hash(sample))
    for sample in (pool[0], pool[135], pool[-1]):
        check("ai hash %s" % sample["id"], sample.get("content_hash") == canon_hash(sample))

    # 7. phone-book canon coherence
    pb = json.load(open("/home/hatch/workspace/jah-ai-models/ai-catalog.json"))
    pb_by_id = {r["ID"]: r for r in pb["records"]}
    drift = [a["id"] for a in pool if a["id"] not in pb_by_id or pb_by_id[a["id"]]["NAME"] != a["name"]]
    check("ai pool matches phone-book canon", not drift, "%d drifted" % len(drift))

    # 8. sitemap validity + coverage
    try:
        for f in ["sitemap.xml", "sitemap-index.xml"] + sorted(glob.glob(os.path.join(ROOT, "sitemap-pairs-*.xml"))):
            xml.dom.minidom.parse(os.path.join(ROOT, f))
        pair_urls = sum(len(re.findall(r"<loc>", open(os.path.join(ROOT, f)).read()))
                        for f in glob.glob(os.path.join(ROOT, "sitemap-pairs-*.xml")))
        check("sitemaps valid XML", True)
        check("pair sitemap covers all pairs", pair_urls == total, "%d vs %d" % (pair_urls, total))
    except Exception as e:
        check("sitemaps valid XML", False, str(e))

    # 9. required machine-readable files exist
    for f in ["matcher-manifest.json", "api.json", "llms.txt", "ai-manifest.json",
              "methodology.html", "data/schemas/pair.schema.json",
              "data/schemas/robot.schema.json", "data/schemas/ai.schema.json",
              "data/schemas/manifest.schema.json"]:
        check("exists " + f, os.path.exists(os.path.join(ROOT, f)))

    # 10. no hard-coded stale counts in api.json description fields
    check("no stale '3000' in api.json", '"pairs_seeded": 3000' not in open(os.path.join(ROOT, "api.json")).read())

    print("\n%d checks, %d failures" % (n_checks[0], len(FAIL)))
    if FAIL:
        print("FAILURES:", FAIL)
        sys.exit(1)
    print("ALL QA CHECKS PASSED")


if __name__ == "__main__":
    main()
