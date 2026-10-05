#!/usr/bin/env python3
"""Build matcher-manifest.json — the ONE authoritative count source for the
Signature AI to Robot Matcher — and refresh the count fields of api.json.

Every visible count on the site must read the manifest. Rebuilt by the pair
drip after every run (see code/drip_pairs.py). Fails loudly on any
inconsistency.
"""
import gzip
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    state = json.load(open(os.path.join(ROOT, "data/state.json")))
    total_pairs = state["next_index"] - 1
    pool = json.load(open(os.path.join(ROOT, "data/ai_pool.json")))
    bodies = json.load(open(os.path.join(ROOT, "data/bodies.json")))
    idx_path = os.path.join(ROOT, "data/index/pairs.idx.json.gz")
    idx = json.load(gzip.open(idx_path, "rt"))

    # ---- integrity assertions (build fails loudly) ----
    assert len(idx) == total_pairs, \
        "index rows %d != state pairs %d" % (len(idx), total_pairs)
    ids = [r[0] for r in idx]
    assert len(set(ids)) == len(ids), "duplicate pair ids in index"
    nums = sorted(int(i.rsplit("-", 1)[1]) for i in ids)
    assert nums == list(range(1, total_pairs + 1)), "pair ids not contiguous 1..%d" % total_pairs
    body_ids = {b["id"] for b in bodies}
    ai_ids = {a["id"] for a in pool}
    # spot-check first/middle/last index rows resolve (full orphan scan lives in qa)
    for r in (idx[0], idx[len(idx) // 2], idx[-1]):
        assert r[0].startswith("JAH-PAIR-"), "bad pair id in index: %r" % r[0]

    ai_families = dict(Counter(a["family"] for a in pool))
    body_classes = dict(Counter(b["class"] for b in bodies))

    manifest = {
        "manifest": "matcher-manifest",
        "site_id": "SIGNATURE-AI-ROBOT-MATCHER",
        "site_name": "The Signature AI to Robot Matcher",
        "site_url": BASE,
        "site_version": "1.0",
        "archive_version": "2026-10-03",
        "schema_version": "JAH-PAIR-RECORD/1.0",
        "total_pairs": total_pairs,
        "earliest_pair_id": "JAH-PAIR-000001",
        "latest_pair_id": "JAH-PAIR-%06d" % total_pairs,
        "pair_id_scheme": "JAH-PAIR-###### (catalog) / JAH-MIX-XXXXXX (user-forged)",
        "total_ais": len(pool),
        "ai_id_scheme": "JAH-AI-###-### (canonical Signature AI Phone Book IDs)",
        "ai_families": ai_families,
        "total_robot_bodies": len(bodies),
        "body_id_scheme": "JAH-BOT-######",
        "body_family_scheme": "JAH-BOTFAM-##",
        "body_classes": body_classes,
        "goal_pairs": 1000000,
        "pairs_remaining": 1000000 - total_pairs,
        "index_version": "pairs.idx/1.0",
        "index_hash": sha256_file(idx_path),
        "index_rows": len(idx),
        "matcher_version": "pair-engine/1.0",
        "generator_version": "gen_pairs/1.0",
        "score_method": {
            "range": [0, 100],
            "meaning": "documented concept fit only — NOT engineering feasibility, "
                       "safety rating, production readiness, certification, or "
                       "physical compatibility",
            "formula": "55 + int(25 * shared_tags / union_tags) + pair_factor(0..19), capped at 100",
            "factors": ["capability-tag overlap (AI skills vs body hardware)",
                        "temperament fit (documented rationale)",
                        "task fit (mission vs body hardware)",
                        "deterministic pair factor 0-19"],
            "deterministic": True,
        },
        "status_vocabulary": ["CONCEPT", "NOT_SIMULATED", "NOT_MANUFACTURED",
                              "NOT_TESTED", "DOCUMENTED", "RETIRED"],
        "concept_fit_boundary": "A high concept-fit score is never approval to build, "
                                "deploy, or certify a robot. Concept match, technical "
                                "compatibility, and physical validation are independent statuses.",
        "last_updated": TODAY,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    out = os.path.join(ROOT, "matcher-manifest.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print("wrote %s: %d pairs, %d AIs, %d bodies" % (out, total_pairs, len(pool), len(bodies)))

    # ---- refresh api.json count fields (descriptive fields preserved) ----
    api_path = os.path.join(ROOT, "api.json")
    api = json.load(open(api_path))
    api["ai_count"] = len(pool)
    api["bodies"] = len(bodies)
    api["pairs_seeded"] = total_pairs
    api["manifest"] = "matcher-manifest.json"
    api["last_updated"] = TODAY
    with open(api_path, "w", encoding="utf-8") as f:
        json.dump(api, f, indent=1)
        f.write("\n")
    print("refreshed %s counts" % api_path)

    # ---- stamp the last-known real pair count into index.html's raw HTML ----
    # (universal loading pattern: counters must never boot as bare "…";
    # JS paintCounter() overwrites this live at boot)
    idx_path_html = os.path.join(ROOT, "index.html")
    html = open(idx_path_html, encoding="utf-8").read()
    stamped = re.sub(r'<b id="paircount">[^<]*</b>',
                     '<b id="paircount">%s</b>' % f"{total_pairs:,}",
                     html, count=1)
    n_matches = len(re.findall(r'<b id="paircount">[^<]*</b>', html))
    assert n_matches == 1, "paircount stamp target count=%d in index.html" % n_matches
    if stamped == html:
        print("index.html paircount already stamped: %s" % f"{total_pairs:,}")
    else:
        open(idx_path_html, "w", encoding="utf-8").write(stamped)
        print("stamped index.html paircount: %s" % f"{total_pairs:,}")


if __name__ == "__main__":
    main()
