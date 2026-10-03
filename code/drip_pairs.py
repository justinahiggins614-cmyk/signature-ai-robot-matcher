#!/usr/bin/env python3
"""STEP 4: Drip new pairs: python3 code/drip_pairs.py --n 1000

Reads data/state.json next_index, generates the next N pairs (100 per chunk,
merging into a partially-filled tail chunk if needed), rebuilds the index,
and advances next_index.

Safety:
- 800MB guard: estimates new bytes (in-memory gzip of merged chunks) and
  refuses with "GUARD TRIPPED" + exit 1 if data/ would exceed 800MB.
- Idempotent-safe: pair_from_id(n) is deterministic, so existing IDs are never
  regenerated differently; chunks below the write range are never touched;
  state.json advances only after successful writes.
"""
import argparse
import gzip
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from gen_pairs import pair_from_id, chunk_path, rebuild_index, CHUNK_SIZE

GUARD_BYTES = 800_000_000


def dir_size(path):
    total = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            total += os.path.getsize(os.path.join(dp, fn))
    return total


def read_chunk_pairs(chunk_n):
    path = chunk_path(chunk_n)
    if not os.path.exists(path):
        return {}
    out = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            out[p["id"]] = p
    return out


def merged_chunk_bytes(chunk_n, new_pairs):
    existing = read_chunk_pairs(chunk_n)
    for p in new_pairs:
        existing[p["id"]] = p  # deterministic: identical content if re-run
    ordered = [existing[k] for k in sorted(existing)]
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        for p in ordered:
            gz.write((json.dumps(p, separators=(",", ":")) + "\n").encode("utf-8"))
    return buf.getvalue(), ordered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True, help="number of new pairs")
    args = ap.parse_args()
    if args.n <= 0:
        print("nothing to do")
        return

    # coherence gate: AI profiles must match the phone-book canon verbatim
    chk = subprocess.run([sys.executable,
                          os.path.join(HERE, "check_coherence.py")],
                         capture_output=True, text=True)
    print(chk.stdout.strip())
    if chk.returncode != 0:
        print("COHERENCE GATE FAILED — refusing to drip", file=sys.stderr)
        sys.exit(2)

    state_path = os.path.join(ROOT, "data", "state.json")
    with open(state_path, encoding="utf-8") as f:
        next_index = json.load(f)["next_index"]

    new_pairs = [pair_from_id(n) for n in range(next_index, next_index + args.n)]

    # group by chunk
    by_chunk = {}
    for n, p in zip(range(next_index, next_index + args.n), new_pairs):
        chunk_n = (n - 1) // CHUNK_SIZE + 1
        by_chunk.setdefault(chunk_n, []).append(p)

    # guard: estimate bytes the merged chunks will occupy
    merged = {c: merged_chunk_bytes(c, ps) for c, ps in by_chunk.items()}
    est_new = sum(len(blob) for blob, _ in merged.values())
    current = dir_size(os.path.join(ROOT, "data"))
    # subtract bytes of chunks we will replace (they're inside current)
    for c in merged:
        p = chunk_path(c)
        if os.path.exists(p):
            est_new -= os.path.getsize(p)
    if current + max(0, est_new) > GUARD_BYTES:
        print("GUARD TRIPPED: data dir would exceed 800MB "
              "(current=%d, estimated new=%d)" % (current, est_new))
        sys.exit(1)

    # write chunks (only the new/merged range)
    for c, (blob, _ordered) in sorted(merged.items()):
        with open(chunk_path(c), "wb") as f:
            f.write(blob)

    indexed = rebuild_index()
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump({"next_index": next_index + args.n}, f, separators=(",", ":"))

    # refresh machine-readable feed, modular sitemaps, and static bot tables
    for script in ("build_pairs_feed.py", "build_sitemap.py", "build_pairs_table.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("WARNING: %s failed: %s" % (script, (r.stderr or r.stdout).strip()))
        else:
            print(r.stdout.strip())

    print("drip +%d pairs (JAH-PAIR-%06d..JAH-PAIR-%06d), %d chunk(s) written, "
          "index rows: %d, next_index=%d"
          % (args.n, next_index, next_index + args.n - 1,
             len(merged), indexed, next_index + args.n))


if __name__ == "__main__":
    main()
