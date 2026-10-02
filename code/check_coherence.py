#!/usr/bin/env python3
"""Coherence check: the phone book (~/workspace/jah-ai-models/ai-catalog.json)
is the single source of truth for AI profiles. This script asserts that
data/ai_pool.json carries the canon VERBATIM (id, name, description, role,
kind) and that every stored pair's ai_id/ai_name matches canon.

Exits 0 on coherence, 1 with details on any drift. Wired into
code/drip_pairs.py so a drift can never be pushed.
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CANON = "/home/hatch/workspace/jah-ai-models/ai-catalog.json"

CANON_FIELDS = (("ID", "id"), ("NAME", "name"), ("DESCRIPTION", "description"),
                ("ROLE", "role"), ("TYPE", "kind"))


def main():
    errors = []
    with open(CANON, encoding="utf-8") as f:
        records = json.load(f)["records"]
    canon = {r["ID"]: r for r in records}

    with open(os.path.join(ROOT, "data", "ai_pool.json"), encoding="utf-8") as f:
        pool = json.load(f)

    if len(pool) != len(canon):
        errors.append("pool size %d != canon size %d" % (len(pool), len(canon)))
    seen = set()
    for p in pool:
        seen.add(p["id"])
        r = canon.get(p["id"])
        if r is None:
            errors.append("pool id %s not in canon" % p["id"])
            continue
        for ck, pk in CANON_FIELDS:
            if p.get(pk) != r.get(ck, ""):
                errors.append("pool %s field %s drifted: pool=%r canon=%r"
                              % (p["id"], pk, p.get(pk), r.get(ck, "")))
    missing = set(canon) - seen
    if missing:
        errors.append("canon ids missing from pool: %s"
                      % sorted(missing)[:5])

    # spot-check stored pair chunks: ai_id/ai_name must match canon
    pairs_dir = os.path.join(ROOT, "data", "pairs")
    checked = 0
    if os.path.isdir(pairs_dir):
        for fn in sorted(os.listdir(pairs_dir)):
            if not fn.endswith(".jsonl.gz"):
                continue
            with gzip.open(os.path.join(pairs_dir, fn), "rt",
                           encoding="utf-8") as f:
                for line in f:
                    p = json.loads(line)
                    r = canon.get(p["ai_id"])
                    if r is None:
                        errors.append("pair %s ai_id %s not in canon"
                                      % (p["id"], p["ai_id"]))
                    elif p["ai_name"] != r["NAME"]:
                        errors.append("pair %s ai_name drifted: %r vs canon %r"
                                      % (p["id"], p["ai_name"], r["NAME"]))
                    checked += 1
    if not checked:
        errors.append("no pair chunks found to check")

    if errors:
        print("COHERENCE FAILED (%d problems):" % len(errors))
        for e in errors[:20]:
            print(" -", e)
        return 1
    print("coherence OK: %d AIs verbatim vs canon, %d pair records checked"
          % (len(pool), checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
