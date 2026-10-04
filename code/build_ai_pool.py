#!/usr/bin/env python3
"""STEP 1: Extract the 270 embedded AIs from the phone-book catalog into
data/ai_pool.json.

Each record carries the phone-book canon profile VERBATIM (id, name,
description, role, kind) plus the derived match-engine fields (family, tags).
The canon is ~/workspace/jah-ai-models/ai-catalog.json — the single source of
truth. code/check_coherence.py asserts the pool never drifts from canon.

Tags are derived deterministically from each AI's name+description via a fixed
keyword->capability mapping (tag vocabulary shared with the robot bodies so the
match engine can compute real overlaps). No randomness anywhere.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = "/home/hatch/workspace/jah-ai-models/ai-catalog.json"

# keyword (lowercase, matched as substring on name + " " + description)
# -> capability tags shared with the robot-body vocabulary
KEYWORD_TAGS = [
    ("surg", ["sterile", "delicate-manipulation", "surgical", "precision"]),
    ("medic", ["sterile", "patient-care", "precise"]),
    ("doctor", ["sterile", "patient-care", "precise"]),
    ("nurse", ["patient-care", "delicate-manipulation", "sterile"]),
    ("pharma", ["sterile", "precise", "quality-control"]),
    ("dent", ["sterile", "delicate-manipulation", "precision"]),
    ("therap", ["patient-care", "communication", "companion"]),
    ("psych", ["communication", "companion", "counseling"]),
    ("counselor", ["communication", "companion", "counseling"]),
    ("veterinar", ["patient-care", "delicate-manipulation", "agri"]),
    ("first aid", ["patient-care", "rescue", "rugged"]),
    ("elder", ["patient-care", "mobility-assist", "companion"]),
    ("factory", ["heavy-lift", "industrial", "assembly"]),
    ("manufactur", ["heavy-lift", "assembly", "industrial"]),
    ("weld", ["heavy-lift", "industrial", "precision"]),
    ("assembl", ["precision", "assembly", "industrial"]),
    ("warehouse", ["logistics", "heavy-lift", "sorting"]),
    ("forklift", ["heavy-lift", "logistics", "industrial"]),
    ("logistic", ["logistics", "cargo", "transport"]),
    ("cargo", ["cargo", "heavy-lift", "logistics"]),
    ("packag", ["sorting", "packaging", "logistics"]),
    ("sort", ["sorting", "precision", "logistics"]),
    ("quality control", ["quality-control", "inspection", "precision"]),
    ("inspect", ["inspection", "precision", "quality-control"]),
    ("construction", ["heavy-lift", "construction", "rugged"]),
    ("crane", ["heavy-lift", "construction", "rugged"]),
    ("demolition", ["heavy-lift", "construction", "hazardous"]),
    ("bridge", ["construction", "inspection", "heavy-lift"]),
    ("tunnel", ["construction", "all-terrain", "rugged"]),
    ("dam ", ["construction", "inspection", "underwater"]),
    ("roof", ["construction", "climbing", "inspection"]),
    ("farm", ["agri", "all-terrain", "harvest"]),
    ("agricultur", ["agri", "all-terrain", "harvest"]),
    ("crop", ["agri", "harvest", "spraying"]),
    ("harvest", ["harvest", "agri", "delicate-manipulation"]),
    ("irrigat", ["irrigation", "agri", "all-terrain"]),
    ("livestock", ["agri", "all-terrain", "monitoring"]),
    ("soil", ["agri", "inspection", "all-terrain"]),
    ("greenhouse", ["agri", "delicate-manipulation", "monitoring"]),
    ("pest", ["agri", "spraying", "inspection"]),
    ("drone", ["aerial", "surveillance", "long-endurance"]),
    ("aerial", ["aerial", "surveillance", "mapping"]),
    ("aviation", ["aerial", "navigation", "long-endurance"]),
    ("satellite", ["aerial", "mapping", "long-endurance"]),
    ("space", ["space", "rugged", "long-endurance"]),
    ("lunar", ["space", "all-terrain", "rugged"]),
    ("mars", ["space", "all-terrain", "exploration"]),
    ("martian", ["space", "all-terrain", "exploration"]),
    ("submarine", ["underwater", "submersible", "long-endurance"]),
    ("underwater", ["underwater", "submersible", "inspection"]),
    ("marine", ["underwater", "submersible", "mapping"]),
    ("ocean", ["underwater", "submersible", "long-endurance"]),
    ("diver", ["underwater", "submersible", "delicate-manipulation"]),
    ("pipeline", ["inspection", "underwater", "rugged"]),
    ("rescue", ["rescue", "rugged", "all-terrain"]),
    ("search and rescue", ["rescue", "all-terrain", "rugged"]),
    ("disaster", ["rescue", "hazardous", "rugged"]),
    ("firefight", ["hazardous", "rescue", "rugged"]),
    ("hazmat", ["hazardous", "inspection", "rugged"]),
    ("explosive", ["hazardous", "delicate-manipulation", "rugged"]),
    ("bomb", ["hazardous", "delicate-manipulation", "rugged"]),
    ("security", ["surveillance", "security", "patrol"]),
    ("surveillance", ["surveillance", "night-vision", "security"]),
    ("patrol", ["patrol", "surveillance", "all-terrain"]),
    ("border", ["patrol", "surveillance", "all-terrain"]),
    ("perimeter", ["patrol", "security", "surveillance"]),
    ("crowd", ["security", "communication", "patrol"]),
    ("escort", ["security", "mobility", "patrol"]),
    ("recon", ["surveillance", "aerial", "stealth"]),
    ("spy", ["surveillance", "stealth", "night-vision"]),
    ("companion", ["companion", "communication", "entertainment"]),
    ("friend", ["companion", "communication", "entertainment"]),
    ("entertain", ["entertainment", "communication", "companion"]),
    ("storytell", ["entertainment", "communication", "education"]),
    ("teacher", ["education", "communication", "companion"]),
    ("tutor", ["education", "communication", "companion"]),
    ("coach", ["education", "communication", "mobility"]),
    ("chef", ["cooking", "delicate-manipulation", "domestic"]),
    ("cook", ["cooking", "domestic", "delicate-manipulation"]),
    ("clean", ["cleaning", "domestic", "mobility"]),
    ("laundry", ["domestic", "cleaning", "sorting"]),
    ("garden", ["gardening", "agri", "delicate-manipulation"]),
    ("pet ", ["pet-care", "companion", "domestic"]),
    ("dog", ["pet-care", "companion", "all-terrain"]),
    ("child", ["child-safe", "companion", "education"]),
    ("baby", ["child-safe", "patient-care", "delicate-manipulation"]),
    ("home", ["domestic", "mobility", "cleaning"]),
    ("housekeep", ["domestic", "cleaning", "organizing"]),
    ("organiz", ["organizing", "sorting", "domestic"]),
    ("shop", ["shopping", "logistics", "domestic"]),
    ("navigat", ["navigation", "mapping", "mobility"]),
    ("map", ["mapping", "navigation", "exploration"]),
    ("explor", ["exploration", "all-terrain", "mapping"]),
    ("cave", ["exploration", "all-terrain", "rugged"]),
    ("archaeolog", ["exploration", "delicate-manipulation", "mapping"]),
    ("geolog", ["exploration", "rugged", "inspection"]),
    ("weather", ["monitoring", "aerial", "long-endurance"]),
    ("climate", ["monitoring", "long-endurance", "agri"]),
    ("solar", ["inspection", "aerial", "long-endurance"]),
    ("wind turbine", ["inspection", "aerial", "climbing"]),
    ("electric", ["maintenance", "repair", "precision"]),
    ("plumb", ["repair", "maintenance", "domestic"]),
    ("mechanic", ["repair", "maintenance", "industrial"]),
    ("repair", ["repair", "maintenance", "delicate-manipulation"]),
    ("mainten", ["maintenance", "inspection", "repair"]),
    ("engineer", ["precision", "assembly", "industrial"]),
    ("architect", ["construction", "precision", "mapping"]),
    ("design", ["precision", "delicate-manipulation", "creativity"]),
    ("artist", ["creativity", "delicate-manipulation", "entertainment"]),
    ("music", ["entertainment", "communication", "creativity"]),
    ("game", ["entertainment", "communication", "creativity"]),
    ("sport", ["mobility", "all-terrain", "entertainment"]),
    ("fitness", ["mobility", "companion", "monitoring"]),
    ("driver", ["transport", "navigation", "mobility"]),
    ("pilot", ["aerial", "navigation", "transport"]),
    ("sailor", ["underwater", "navigation", "transport"]),
    ("captain", ["navigation", "transport", "communication"]),
    ("delivery", ["delivery", "last-mile", "logistics"]),
    ("courier", ["delivery", "last-mile", "mobility"]),
    ("postal", ["delivery", "logistics", "sorting"]),
    ("lawyer", ["communication", "counseling", "precision"]),
    ("legal", ["communication", "counseling", "precision"]),
    ("judge", ["communication", "counseling", "precision"]),
    ("accountant", ["precision", "organizing", "communication"]),
    ("banker", ["precision", "communication", "security"]),
    ("financ", ["precision", "communication", "security"]),
    ("scientist", ["precision", "inspection", "exploration"]),
    ("chemist", ["hazardous", "sterile", "precision"]),
    ("biolog", ["sterile", "inspection", "exploration"]),
    ("physic", ["precision", "exploration", "industrial"]),
    ("astronom", ["space", "mapping", "long-endurance"]),
    ("meteorolog", ["monitoring", "aerial", "long-endurance"]),
    ("journalist", ["communication", "surveillance", "mapping"]),
    ("photograph", ["aerial", "surveillance", "mapping"]),
    ("librarian", ["organizing", "education", "communication"]),
    ("historian", ["education", "communication", "exploration"]),
    ("translator", ["communication", "education", "companion"]),
    ("receptionist", ["communication", "domestic", "organizing"]),
    ("assistant", ["general-assist", "communication", "organizing"]),
    ("butler", ["domestic", "communication", "organizing"]),
    ("maid", ["domestic", "cleaning", "organizing"]),
    ("nanny", ["child-safe", "companion", "domestic"]),
    ("barber", ["delicate-manipulation", "domestic", "precision"]),
    ("tailor", ["delicate-manipulation", "precision", "domestic"]),
    ("jeweler", ["delicate-manipulation", "precision", "sterile"]),
    ("watchmaker", ["delicate-manipulation", "precision", "sterile"]),
    ("locksmith", ["delicate-manipulation", "precision", "security"]),
    ("guard", ["security", "patrol", "surveillance"]),
    ("soldier", ["rugged", "all-terrain", "security"]),
    ("warrior", ["rugged", "all-terrain", "security"]),
    ("knight", ["rugged", "security", "companion"]),
    ("pirate", ["underwater", "navigation", "rugged"]),
    ("ninja", ["stealth", "mobility", "surveillance"]),
    ("samurai", ["precision", "delicate-manipulation", "companion"]),
    ("wizard", ["creativity", "communication", "entertainment"]),
    ("vader", ["command", "security", "companion"]),
    ("ultron", ["industrial", "precision", "command"]),
    ("voltron", ["command", "heavy-lift", "teamwork"]),
    ("jarvis", ["domestic", "organizing", "communication"]),
    ("skynet", ["surveillance", "command", "security"]),
    ("t-800", ["rugged", "security", "all-terrain"]),
    ("terminator", ["rugged", "security", "all-terrain"]),
    ("deterministic", ["precision", "logic", "industrial"]),
    ("probabilistic", ["precision", "logic", "monitoring"]),
    ("logic", ["precision", "logic", "industrial"]),
    ("swarm", ["swarm-link", "aerial", "coordination"]),
    ("hive", ["swarm-link", "coordination", "agri"]),
    ("coordinat", ["coordination", "swarm-link", "logistics"]),
    ("fleet", ["coordination", "logistics", "transport"]),
    ("night", ["night-vision", "surveillance", "stealth"]),
    ("thermal", ["thermal", "inspection", "night-vision"]),
    ("tactile", ["tactile", "delicate-manipulation", "precision"]),
    ("climb", ["climbing", "inspection", "rugged"]),
    ("swim", ["underwater", "submersible", "mobility"]),
    ("fly", ["aerial", "mobility", "long-endurance"]),
    ("run", ["mobility", "all-terrain", "speed"]),
    ("lift", ["heavy-lift", "industrial", "rugged"]),
    ("carry", ["heavy-lift", "logistics", "mobility"]),
    ("dig", ["construction", "heavy-lift", "rugged"]),
    ("mine", ["construction", "hazardous", "underground"]),
    ("tunnel", ["construction", "all-terrain", "rugged"]),
    ("waste", ["cleaning", "hazardous", "logistics"]),
    ("recycl", ["sorting", "cleaning", "logistics"]),
    ("energy", ["long-endurance", "monitoring", "industrial"]),
    ("nuclear", ["hazardous", "inspection", "industrial"]),
    ("oil", ["hazardous", "inspection", "industrial"]),
    ("gas", ["hazardous", "inspection", "monitoring"]),
    ("power plant", ["industrial", "monitoring", "hazardous"]),
]

FAMILY_FALLBACK = {
    "system": ["precision", "logic", "coordination"],
    "persona": ["communication", "companion", "entertainment"],
    "domain": ["general-assist", "communication", "organizing"],
}


def derive_tags(name, description):
    text = (name + " " + description).lower()
    tags = []
    for kw, tlist in KEYWORD_TAGS:
        if kw in text:
            tags.extend(tlist)
    # dedupe, preserve order
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return sorted(out)


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    records = catalog["records"]
    pool = []
    for r in records:
        ai_id = r["ID"]
        name = r["NAME"]
        family = r.get("TYPE", "domain").lower()
        if family not in ("system", "persona", "domain"):
            family = "domain"
        tags = derive_tags(name, r.get("DESCRIPTION", ""))
        if not tags:
            tags = FAMILY_FALLBACK[family]
        # Canon profile carried verbatim — coherence with the phone book.
        # Enrichment fields (added 2026-10-03) are additive identity metadata only.
        rec = {"id": ai_id, "name": name,
               "description": r.get("DESCRIPTION", ""),
               "role": r.get("ROLE", ""),
               "kind": r.get("TYPE", ""),
               "family": family, "tags": tags,
               "phone_book_id": ai_id,
               "phone_book_url": ("https://justinahiggins614-cmyk.github.io/"
                                  "jah-ai-models/#" + ai_id),
               "version": "1.0",
               "created": "2026-10-02",
               "canonical_url": ("https://justinahiggins614-cmyk.github.io/"
                                 "jah-ai-models/#" + ai_id)}
        import hashlib as _hl
        rec["content_hash"] = _hl.sha256(
            json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        pool.append(rec)
    # deterministic order: by id
    pool.sort(key=lambda x: x["id"])
    out_path = os.path.join(ROOT, "data", "ai_pool.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pool, f, separators=(",", ":"))
    print("wrote", out_path, len(pool), "AIs")
    assert len(pool) == len(records), len(pool)
    assert len({p["id"] for p in pool}) == len(records)


if __name__ == "__main__":
    main()
