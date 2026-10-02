#!/usr/bin/env python3
"""STEP 3: Deterministic AI+robot-body matching engine.

pair_from_id(n) for n = 1..1000000 always yields the SAME pair, byte-identical
across runs. Seeds data/pairs/ (100 records per chunk) and builds
data/index/pairs.idx.json.gz.
"""
import gzip
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHUNK_SIZE = 100
CREATED = "2026-10-02"

# 32 fixed original mission strings + a verb phrase tying the mission to action.
MISSIONS = [
    ("harbor cargo survey", "scan and log every container"),
    ("home elder companionship", "keep a steady, friendly presence"),
    ("greenhouse pollination run", "brush each blossom with care"),
    ("night warehouse patrol", "walk the aisles and check every seal"),
    ("riverbank erosion mapping", "chart the waterline meter by meter"),
    ("hospital linen delivery", "ferry fresh linen to every ward"),
    ("solar farm panel inspection", "scan each panel for hot spots"),
    ("orchard harvest sweep", "pick only the ripe fruit"),
    ("subway tunnel safety check", "sniff the air and scan the walls"),
    ("school hallway monitor duty", "greet students and watch the corridors"),
    ("offshore rig bolt audit", "torque-check every flange"),
    ("forest fire watch", "sniff for smoke before flames show"),
    ("pharmacy restock round", "shelve medicine without error"),
    ("construction site material lift", "stage steel where the crew needs it"),
    ("museum after-hours guard", "drift silently past the exhibits"),
    ("wheat field pest scouting", "flag every stressed plant"),
    ("airport runway debris scan", "sweep the tarmac for hazards"),
    ("nursing home evening rounds", "check in on every resident"),
    ("dam intake grate cleaning", "clear debris from the flow"),
    ("vineyard frost alert patrol", "read the cold air over the vines"),
    ("data center thermal sweep", "find the hot rack before it fails"),
    ("playground safety inspection", "test every swing and slide"),
    ("oil pipeline leak survey", "sniff out the faintest seep"),
    ("library book reshelving", "file every returned book"),
    ("marina hull cleaning", "scrub below the waterline"),
    ("bakery dawn prep shift", "measure, mix, and portion dough"),
    ("mountain trail rescue standby", "carry supplies up the steep path"),
    ("aquarium tank maintenance", "clean glass and check water chemistry"),
    ("stadium post-game cleanup", "collect what forty thousand fans left behind"),
    ("observatory dome night watch", "track the sky and guard the optics"),
    ("grain silo level sounding", "measure every bin to the centimeter"),
    ("coastal cliff nest census", "count seabirds without disturbing them"),
]

AI_POOL = None
BODIES = None


def load_inputs():
    global AI_POOL, BODIES
    if AI_POOL is None:
        with open(os.path.join(ROOT, "data", "ai_pool.json"), encoding="utf-8") as f:
            AI_POOL = json.load(f)
        with open(os.path.join(ROOT, "data", "bodies.json"), encoding="utf-8") as f:
            BODIES = json.load(f)
    return AI_POOL, BODIES


def h_int(key, mod):
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % mod


def _pick(key, options):
    return options[h_int(key, len(options))]


def capability_rationale(ai, body, overlap):
    ai_tags = ai["tags"]
    body_tags = body["tags"]
    if overlap:
        shared = ", ".join(sorted(set(overlap))[:3])
        return ("%s's strengths (%s) meet the %s's %s-class build head-on: "
                "they share %s, so the mind and the shell pull in the same "
                "direction from the first boot."
                % (ai["name"], ", ".join(ai_tags[:3]),
                   body["name"], body["class"].replace("-", " "), shared))
    return ("%s brings %s expertise to the %s's %s-class frame — a deliberate "
            "mismatch that covers more ground than either could alone, with the "
            "AI's judgment compensating for what the body was never built to do."
            % (ai["name"], ai_tags[0],
               body["name"], body["class"].replace("-", " ")))


def temperament_rationale(ai):
    fam = ai["family"]
    if fam == "system":
        return ("As a system mind, %s treats every mission as a formal problem: "
                "no panic, no improvisation, just steady rule-bound execution "
                "that operators can audit line by line." % ai["name"])
    if fam == "persona":
        return ("As a persona interpretation, %s carries a presence people feel "
                "the moment the shell moves — authority and theater that make a "
                "visible robot worth watching instead of worth fearing."
                % ai["name"])
    return ("As a working specialist, %s stays focused on the job, narrates its "
            "own work in plain words, and hands control back to its human "
            "operator the instant anything looks off." % ai["name"])


def task_rationale(body, mission, verb):
    actuator = body["actuators"][0].rsplit(" (", 1)[0]
    sensor = body["sensors"][0]
    return ("On the %s, the %s puts its %s and %s to work to %s — "
            "the mission's demands and the body's hardware line up "
            "actuator for actuator." % (mission, body["name"], actuator, sensor, verb))


def demo_lines(ai, body, mission, verb, score, n):
    actuator = body["actuators"][h_int("dla%d" % n, len(body["actuators"]))].rsplit(" (", 1)[0]
    actuator2 = body["actuators"][(h_int("dla%d" % n, len(body["actuators"])) + 1) % len(body["actuators"])].rsplit(" (", 1)[0]
    sensor = body["sensors"][h_int("dls%d" % n, len(body["sensors"]))]
    templates = [
        "I am %s, and I run inside the %s body — %s-class, built for real work.",
        "My %s lets me %s without breaking stride.",
        "Through my %s, I read the mission field in full detail before I act.",
        "On %s I keep my %s moving with %s, steady from start to finish.",
        "Matched at %d of 100, this pairing is no accident — ask me anything.",
        "With %s under me and my %s awake, the %s is already underway.",
    ]
    filled = [
        templates[0] % (ai["name"], body["name"], body["class"].replace("-", " ")),
        templates[1] % (actuator, verb),
        templates[2] % (sensor,),
        templates[3] % (mission, body["mobility"], actuator2),
        templates[4] % (score,),
        templates[5] % (body["mobility"], sensor, mission),
    ]
    # deterministic rotation so different pairs read differently
    rot = h_int("dlr%d" % n, len(filled))
    return [filled[(rot + i) % len(filled)] for i in range(5)][:5]


def pair_from_id(n):
    """Deterministic pair record for 1 <= n <= 1000000. Byte-identical always."""
    ai_pool, bodies = load_inputs()
    ai = ai_pool[h_int("ai%d" % n, len(ai_pool))]
    body = bodies[h_int("body%d" % n, len(bodies))]
    mission, verb = MISSIONS[h_int("m%d" % n, len(MISSIONS))]

    a_tags = set(ai["tags"])
    b_tags = set(body["tags"])
    overlap = a_tags & b_tags
    union = a_tags | b_tags
    score = 55 + int(25 * (len(overlap) / max(1, len(union)))) + h_int("s%d" % n, 20)
    score = min(100, score)

    return {
        "id": "JAH-PAIR-%06d" % n,
        "ai_id": ai["id"],
        "ai_name": ai["name"],
        "ai_family": ai["family"],
        "body_id": body["id"],
        "body_name": body["name"],
        "mission": mission,
        "score": score,
        "rationale": {
            "capability": capability_rationale(ai, body, overlap),
            "temperament": temperament_rationale(ai),
            "task": task_rationale(body, mission, verb),
        },
        "demo_lines": demo_lines(ai, body, mission, verb, score, n),
        "created": CREATED,
    }


def chunk_path(chunk_n):
    return os.path.join(ROOT, "data", "pairs", "pairs-c%05d.jsonl.gz" % chunk_n)


def write_chunk(chunk_n, pairs):
    with gzip.open(chunk_path(chunk_n), "wt", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, separators=(",", ":")) + "\n")


def rebuild_index():
    rows = []
    pairs_dir = os.path.join(ROOT, "data", "pairs")
    for fn in sorted(os.listdir(pairs_dir)):
        if not fn.endswith(".jsonl.gz"):
            continue
        chunk_n = int(fn[7:12])
        with gzip.open(os.path.join(pairs_dir, fn), "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                rows.append([p["id"], p["ai_name"], p["body_name"], p["mission"], chunk_n])
    # verify: zero dupes, sorted by pair id
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate pair ids in index"
    rows.sort(key=lambda r: r[0])
    idx_path = os.path.join(ROOT, "data", "index", "pairs.idx.json.gz")
    with gzip.open(idx_path, "wt", encoding="utf-8") as f:
        json.dump(rows, f, separators=(",", ":"))
    return len(rows)


def seed(n_from, n_to):
    """Generate pairs n_from..n_to inclusive, writing full chunks of 100."""
    assert (n_to - n_from + 1) % CHUNK_SIZE == 0, "seed range must be whole chunks"
    pairs = [pair_from_id(n) for n in range(n_from, n_to + 1)]
    ids = [p["id"] for p in pairs]
    assert len(ids) == len(set(ids)), "dupe ids in seed range"
    for i in range(0, len(pairs), CHUNK_SIZE):
        chunk_n = (n_from + i - 1) // CHUNK_SIZE + 1
        write_chunk(chunk_n, pairs[i:i + CHUNK_SIZE])
    with open(os.path.join(ROOT, "data", "state.json"), "w", encoding="utf-8") as f:
        json.dump({"next_index": n_to + 1}, f, separators=(",", ":"))
    return len(pairs)


def main():
    load_inputs()
    count = seed(1, 2000)
    indexed = rebuild_index()
    assert indexed == count == 2000
    print("seeded", count, "pairs in", count // CHUNK_SIZE, "chunks; index rows:", indexed)


if __name__ == "__main__":
    main()
