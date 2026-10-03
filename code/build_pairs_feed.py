#!/usr/bin/env python3
"""Build data/pairs-catalog.json — standardized machine-readable feed of all pairs.

Feed row: {id, ai_id, ai_name, ai_family, body_id, body_name, body_class,
            mission, score, url}. Rebuilt by the pair drip after every run.
"""
import gzip
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/"
CHUNK_SIZE = 100


def main():
    bodies = {b["id"]: b for b in json.load(open(os.path.join(ROOT, "data/bodies.json")))}
    feed = []
    n = 1
    while True:
        path = os.path.join(ROOT, "data/pairs/pairs-c%05d.jsonl.gz" % n)
        if not os.path.exists(path):
            break
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                b = bodies.get(p["body_id"], {})
                feed.append({
                    "id": p["id"],
                    "ai_id": p["ai_id"],
                    "ai_name": p["ai_name"],
                    "ai_family": p["ai_family"],
                    "body_id": p["body_id"],
                    "body_name": p["body_name"],
                    "body_class": b.get("class", ""),
                    "mission": p["mission"],
                    "score": p["score"],
                    "url": BASE + "?pair=" + p["id"],
                })
        n += 1
    out = os.path.join(ROOT, "data/pairs-catalog.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(feed, f, separators=(",", ":"))
    print("pairs-catalog.json: %d pairs" % len(feed))


if __name__ == "__main__":
    main()
