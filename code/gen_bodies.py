#!/usr/bin/env python3
"""STEP 2: Deterministically generate 120 ORIGINAL robot bodies,
JAH-BOT-000001 .. JAH-BOT-000120, across 10 classes (12 each).
All names are invented and trademark-safe. Fully deterministic: re-running
produces byte-identical data/bodies.json.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def h_int(key, mod):
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % mod


def pick(key, options, k=1):
    """Deterministically pick k distinct options for the given key
    (Fisher-Yates shuffle driven by sha256 — no cycles possible)."""
    order = list(range(len(options)))
    for i in range(len(order) - 1, 0, -1):
        j = h_int("%s:shuf:%d" % (key, i), i + 1)
        order[i], order[j] = order[j], order[i]
    return [options[j] for j in order[:min(k, len(options))]]


# 10 classes x 12 invented names each. All names are original coinages.
CLASSES = {
    "domestic-helper": {
        "names": ["Hearthward", "Tidymantle", "Homesteadix", "Larderlane",
                  "Parlorpost", "Kitchenkind", "Atticloft", "Cellardoor",
                  "Windowwell", "Gardenmoss", "Panteypantry", "Chimneychime"],
        "height": (95, 150), "mass": (18, 60), "payload": (5, 25),
        "materials": ["powder-coated aluminum", "soft-touch polymer",
                      "recycled carbon fiber", "antimicrobial silicone"],
        "actuators": [("dual-arm manipulator", 14), ("torso lift column", 1),
                      ("wheeled base drive", 2), ("gripper end-effector", 2)],
        "sensors": ["depth camera", "tactile fingertip array", "voice array",
                    "cliff sensor", "thermal camera", "odor sensor"],
        "power": ["48V lithium-iron battery, 8h runtime",
                  "48V lithium-iron battery, 12h runtime",
                  "docking-station recharge, 10h runtime"],
        "mobility": ["omni-wheel indoor drive", "bipedal indoor walker",
                     "tracked low-profile base"],
        "tags": ["domestic", "cleaning", "cooking", "organizing",
                 "child-safe", "elder-care", "quiet", "companion"],
        "blurb1": "{name} is a domestic helper built for calm, orderly households.",
        "blurb2": "Its {feat} lets it {verb} without ever disturbing the rhythm of the home.",
    },
    "industrial-arm": {
        "names": ["Forgejoint", "Anvilaxis", "Torquetide", "Pistonpact",
                  "Girdergrasp", "Weldwarden", "Presspinnacle", "Lathelord",
                  "Millmaster", "Rivetreach", "Castcrown", "Sparklane"],
        "height": (140, 260), "mass": (120, 900), "payload": (50, 800),
        "materials": ["cast steel", "hardened titanium alloy", "vibration-damping composite"],
        "actuators": [("6-axis articulated arm", 6), ("servo gripper", 2),
                      ("rail-mounted gantry", 1), ("rotary base", 1)],
        "sensors": ["force-torque sensor", "machine-vision camera", "laser scanner",
                    "vibration monitor", "thermal camera"],
        "power": ["480V three-phase mains", "480V three-phase mains with UPS buffer"],
        "mobility": ["floor-bolted pedestal", "ceiling rail traverse", "mobile rail cart"],
        "tags": ["industrial", "heavy-lift", "assembly", "welding",
                 "precision", "rugged", "quality-control"],
        "blurb1": "{name} is a fixed industrial arm engineered for relentless factory duty.",
        "blurb2": "Its {feat} lets it {verb} shift after shift with sub-millimeter repeatability.",
    },
    "medical-assistant": {
        "names": ["Carevelum", "Sanitelle", "Remedyring", "Vitalia",
                  "Mendmere", "Suturestep", "Dosepath", "Calmclinic",
                  "Healharbor", "Tendertrack", "Pulselight", "Asepticus"],
        "height": (110, 175), "mass": (25, 90), "payload": (3, 15),
        "materials": ["medical-grade stainless steel", "antimicrobial silicone",
                      "sealed polycarbonate"],
        "actuators": [("sterile instrument arm", 2), ("medication carousel", 1),
                      ("height-adjust column", 1), ("soft gripper", 2)],
        "sensors": ["sterile-field camera", "vital-signs scanner", "tactile array",
                    "barcode medication reader", "UV sterilization lamp"],
        "power": ["medical-cart battery, 14h runtime", "mains with battery backup"],
        "mobility": ["quiet omni-wheel drive", "bedside rail dock"],
        "tags": ["medical", "sterile", "delicate-manipulation", "patient-care",
                 "precise", "surgical", "quiet", "monitoring"],
        "blurb1": "{name} is a medical assistant designed for clinics and care wards.",
        "blurb2": "Its {feat} lets it {verb} while keeping every surface sterile and every motion gentle.",
    },
    "exploration-rover": {
        "names": ["Dusttrail", "Cratercall", "Ridgerunner", "Stonesight",
                  "Farfield", "Gorgeglide", "Tundratread", "Canyonkeel",
                  "Mesaford", "Glaciergrip", "Badlandbound", "Summitseeker"],
        "height": (60, 140), "mass": (40, 220), "payload": (10, 60),
        "materials": ["titanium spaceframe", "dust-sealed composite",
                      "radiation-tolerant electronics housing"],
        "actuators": [("rocker-bogie wheel set", 6), ("sample-collection arm", 5),
                      ("mast pan-tilt", 2), ("drill auger", 1)],
        "sensors": ["stereo navigation cameras", "lidar", "ground-penetrating radar",
                    "spectrometer", "environmental suite"],
        "power": ["solar array with RTG trickle, multi-year endurance",
                  "high-density battery with solar recharge, 72h endurance"],
        "mobility": ["six-wheel rocker-bogie", "tracked all-terrain crawler"],
        "tags": ["exploration", "all-terrain", "rugged", "long-endurance",
                 "mapping", "inspection", "autonomous", "space"],
        "blurb1": "{name} is an exploration rover built to go where boots cannot.",
        "blurb2": "Its {feat} lets it {verb} for days without human contact.",
    },
    "humanoid-companion": {
        "names": ["Kindredform", "Fellowframe", "Amity", "Warmwelcome",
                  "Heartshell", "Sociable", "Emberkin", "Truetone",
                  "Mirthmeld", "Solace", "Kindred", "Presence"],
        "height": (120, 180), "mass": (30, 85), "payload": (2, 10),
        "materials": ["soft synthetic skin over alloy skeleton", "warm-touch polymer",
                      "expressive LED faceplate"],
        "actuators": [("expressive head and neck", 3), ("gesturing arms", 14),
                      ("bipedal legs", 12), ("hugging torso", 2)],
        "sensors": ["face-tracking camera", "emotion-voice analyzer",
                    "proximity skin", "ambient microphone array"],
        "power": ["swappable torso battery, 10h runtime",
                  "torso battery with wireless charging, 8h runtime"],
        "mobility": ["bipedal walker", "wheeled lower body"],
        "tags": ["companion", "communication", "entertainment", "education",
                 "elder-care", "child-safe", "expressive", "social"],
        "blurb1": "{name} is a humanoid companion made to be present, not just useful.",
        "blurb2": "Its {feat} lets it {verb} in a way that feels genuinely attentive.",
    },
    "aerial-drone": {
        "names": ["Skylark", "Zephyrwing", "Cloudcipher", "Aircurrent",
                  "Gustglider", "Stratoseeker", "Windwhisper", "Horizonhawk",
                  "Updraft", "Featherfall", "Nimbus", "Soarline"],
        "height": (25, 90), "mass": (2, 25), "payload": (1, 12),
        "materials": ["carbon-fiber airframe", "impact-absorbing foam core",
                      "weather-sealed avionics"],
        "actuators": [("brushless rotor set", 4), ("3-axis gimbal", 3),
                      ("cargo release winch", 1), ("tilt-rotor pair", 2)],
        "sensors": ["4K stabilized camera", "thermal imager", "obstacle lidar",
                    "GPS-denied visual odometry", "air-quality probe"],
        "power": ["hot-swap battery packs, 55min flight",
                  "hybrid fuel-cell extender, 4h flight"],
        "mobility": ["quad-rotor hover", "VTOL fixed-wing cruise"],
        "tags": ["aerial", "surveillance", "mapping", "long-endurance",
                 "delivery", "inspection", "swarm-link", "fast"],
        "blurb1": "{name} is an aerial drone tuned for steady eyes in the sky.",
        "blurb2": "Its {feat} lets it {verb} far beyond line of sight.",
    },
    "underwater-drone": {
        "names": ["Tidewalker", "Deepmurmur", "Kelpkeeper", "Currentcaller",
                  "Abyssalight", "Reefranger", "Saltstride", "Bluebell",
                  "Nautinome", "Pelagic", "Undertow", "Coralcraft"],
        "height": (40, 120), "mass": (8, 120), "payload": (2, 20),
        "materials": ["pressure-rated titanium hull", "corrosion-proof composite",
                      "biofouling-resistant coating"],
        "actuators": [("vectored thruster set", 6), ("manipulator claw", 3),
                      ("sample carousel", 1), ("buoyancy engine", 1)],
        "sensors": ["sonar array", "underwater camera with lights",
                    "water-chemistry probe", "doppler velocity log",
                    "magnetic anomaly sensor"],
        "power": ["pressure-tolerant battery, 18h dive",
                  "battery with surface solar recharge, 36h mission"],
        "mobility": ["vectored-thruster ROV", "buoyancy glider"],
        "tags": ["underwater", "submersible", "inspection", "long-endurance",
                 "mapping", "monitoring", "rugged", "stealth"],
        "blurb1": "{name} is an underwater drone that treats the deep as home turf.",
        "blurb2": "Its {feat} lets it {verb} in currents that would tangle a tether.",
    },
    "construction-rig": {
        "names": ["Beamwright", "Foundryfield", "Earthshaper", "Steelstride",
                  "Mortarmason", "Pilondriver", "Trusstrue", "Gradewarden",
                  "Loadbearer", "Sitewarden", "Cranecrest", "Terraforger"],
        "height": (180, 420), "mass": (800, 12000), "payload": (500, 9000),
        "materials": ["structural steel", "wear-plate armor", "hydraulic line shielding"],
        "actuators": [("hydraulic excavator arm", 4), ("dozer blade", 1),
                      ("crane winch", 1), ("compactor plate", 1)],
        "sensors": ["site-survey lidar", "load-cell array", "ground-stability radar",
                    "360-degree camera ring", "proximity safety curtain"],
        "power": ["diesel-electric hybrid drivetrain", "tethered electric with battery buffer"],
        "mobility": ["heavy tracked undercarriage", "articulated wheel loader base"],
        "tags": ["construction", "heavy-lift", "rugged", "all-terrain",
                 "industrial", "hazardous", "long-endurance", "autonomous"],
        "blurb1": "{name} is a construction rig that eats raw terrain for breakfast.",
        "blurb2": "Its {feat} lets it {verb} on sites too rough or risky for crews.",
    },
    "agricultural-bot": {
        "names": ["Fieldfriend", "Cropcaller", "Sowerstone", "Harvesthymn",
                  "Rowrider", "Meadowmere", "Orchardowl", "Tilltide",
                  "Seedpsalm", "Vinewarden", "Pasturepath", "Loamlight"],
        "height": (70, 160), "mass": (30, 180), "payload": (8, 80),
        "materials": ["washdown-rated stainless", "UV-stable polymer",
                      "puncture-proof tires"],
        "actuators": [("picking arm with soft gripper", 6), ("precision sprayer boom", 1),
                      ("seeding drill", 1), ("pruning shear", 2)],
        "sensors": ["multispectral crop camera", "soil-moisture probe",
                    "weed-recognition vision", "weather station",
                    "fruit-ripeness scanner"],
        "power": ["solar-assisted battery, full-day field shift",
                  "swappable field battery packs, 10h shift"],
        "mobility": ["narrow-row wheeled drive", "tracked orchard crawler"],
        "tags": ["agri", "harvest", "all-terrain", "delicate-manipulation",
                 "spraying", "monitoring", "long-endurance", "autonomous"],
        "blurb1": "{name} is an agricultural bot that knows every row by name.",
        "blurb2": "Its {feat} lets it {verb} from dawn dew to dusk without bruising a leaf.",
    },
    "security-sentinel": {
        "names": ["Watchward", "Gatekeeper", "Vigilveil", "Patrolpine",
                  "Sentrygrove", "Nightnoble", "Fenceline", "Lookoutlane",
                  "Shieldshade", "Perimeter", "Beaconbound", "Truestwatch"],
        "height": (100, 200), "mass": (35, 260), "payload": (5, 40),
        "materials": ["ballistic-rated composite shell", "tamper-evident housing",
                      "all-weather seals"],
        "actuators": [("pan-tilt sensor head", 2), ("patrol drive unit", 2),
                      ("non-lethal deterrent emitter", 1), ("barrier arm", 1)],
        "sensors": ["360-degree night-vision cameras", "thermal imager",
                    "microphone array with gunshot detection", "access-badge reader",
                    "motion radar"],
        "power": ["dock-charged battery, 20h patrol",
                  "battery with patrol-dock network, continuous coverage"],
        "mobility": ["wheeled patrol base", "quadruped patrol walker"],
        "tags": ["security", "surveillance", "patrol", "night-vision",
                 "rugged", "all-terrain", "communication", "long-endurance"],
        "blurb1": "{name} is a security sentinel that never blinks on the night shift.",
        "blurb2": "Its {feat} lets it {verb} across a whole facility without fatigue.",
    },
}

# Per-class compute + interfaces + operating envelope.
# Deterministic: new hash keys only — existing fields are untouched.
CLASS_SYSTEMS = {
    "domestic-helper": {
        "compute": ["Signature Cortex-S2 home module · 12 TOPS",
                    "Signature Cortex-S2 home module · 24 TOPS"],
        "interfaces": ["JAH-Link home mesh", "USB-C service port",
                       "voice-array API", "companion-app pairing"],
        "temp": (-10, 40), "ip": "IP20", "extra": "max 1.2 m/s · under 45 dB"},
    "industrial-arm": {
        "compute": ["Signature Forge-X4 cell controller · 60 TOPS",
                    "Signature Forge-X4 cell controller · 120 TOPS"],
        "interfaces": ["EtherCAT fieldbus", "JAH-Link factory mesh",
                       "safety-rated I/O", "USB-C service port"],
        "temp": (0, 55), "ip": "IP54", "extra": "repeatability ±0.05 mm · 24/7 duty"},
    "medical-assistant": {
        "compute": ["Signature Care-M3 clinical module · 30 TOPS",
                    "Signature Care-M3 clinical module · 48 TOPS"],
        "interfaces": ["HL7/FHIR ward link", "JAH-Link clinical mesh",
                       "USB-C service port", "nurse-call integration"],
        "temp": (10, 40), "ip": "IP42", "extra": "max 0.8 m/s · wipe-down safe"},
    "exploration-rover": {
        "compute": ["Signature Trail-R5 field computer · 40 TOPS",
                    "Signature Trail-R5 field computer · 80 TOPS"],
        "interfaces": ["JAH-Link long-range mesh", "satellite uplink",
                       "USB-C service port", "payload CAN bus"],
        "temp": (-40, 60), "ip": "IP67", "extra": "multi-day autonomy · dust-sealed"},
    "humanoid-companion": {
        "compute": ["Signature Hearth-C2 social module · 20 TOPS",
                    "Signature Hearth-C2 social module · 36 TOPS"],
        "interfaces": ["JAH-Link home mesh", "companion-app pairing",
                       "voice-array API", "USB-C service port"],
        "temp": (0, 40), "ip": "IP20", "extra": "max 1.0 m/s · soft-touch safe"},
    "aerial-drone": {
        "compute": ["Signature Sky-A6 flight computer · 25 TOPS",
                    "Signature Sky-A6 flight computer · 50 TOPS"],
        "interfaces": ["JAH-Link swarm mesh", "ground-station link",
                       "USB-C service port", "payload quick-release bus"],
        "temp": (-20, 50), "ip": "IP43", "extra": "wind tolerance 12 m/s · geofenced"},
    "underwater-drone": {
        "compute": ["Signature Depth-U4 marine computer · 25 TOPS",
                    "Signature Depth-U4 marine computer · 50 TOPS"],
        "interfaces": ["acoustic modem link", "tether comms",
                       "USB-C service port (deck)", "payload CAN bus"],
        "temp": (-2, 35), "ip": "IP68", "extra": "rated 300 m depth · 18 h dive"},
    "construction-rig": {
        "compute": ["Signature Site-C8 heavy controller · 70 TOPS",
                    "Signature Site-C8 heavy controller · 140 TOPS"],
        "interfaces": ["JAH-Link site mesh", "fleet telematics",
                       "CAN bus", "USB-C service port"],
        "temp": (-25, 55), "ip": "IP65", "extra": "all-terrain · rollover protected"},
    "agricultural-bot": {
        "compute": ["Signature Field-G4 agri computer · 30 TOPS",
                    "Signature Field-G4 agri computer · 60 TOPS"],
        "interfaces": ["JAH-Link field mesh", "farm-management API",
                       "USB-C service port", "implement ISOBUS"],
        "temp": (-10, 50), "ip": "IP65", "extra": "washdown safe · full-day shift"},
    "security-sentinel": {
        "compute": ["Signature Watch-S5 sentinel module · 40 TOPS",
                    "Signature Watch-S5 sentinel module · 80 TOPS"],
        "interfaces": ["JAH-Link security mesh", "VMS integration",
                       "USB-C service port", "alarm-panel relay"],
        "temp": (-30, 55), "ip": "IP55", "extra": "20 h patrol · night-vision standard"},
}


def build_systems(class_key, body_id):
    sys = CLASS_SYSTEMS[class_key]
    compute = sys["compute"][h_int(body_id + ":cpu", len(sys["compute"]))]
    interfaces = pick(body_id + ":if", sys["interfaces"],
                      k=3)
    tlo, thi = sys["temp"]
    operating_limits = ("%d°C to %d°C · %s · %s"
                        % (tlo, thi, sys["ip"], sys["extra"]))
    return compute, interfaces, operating_limits


FEATURE_VERB = {
    "domestic-helper": [("soft-touch polymer shell", "tidy, cook, and organize"),
                        ("tactile fingertip array", "handle fragile dishes and laundry"),
                        ("cliff sensor suite", "roam stairs-free floors safely")],
    "industrial-arm": [("force-torque sensing", "seat parts and fasten bolts"),
                      ("machine-vision guidance", "spot defects and align workpieces"),
                      ("vibration-damping frame", "hold tolerances through heavy cuts")],
    "medical-assistant": [("sterile instrument arms", "pass tools and prep trays"),
                          ("vital-signs scanner", "watch patients between rounds"),
                          ("UV sterilization lamp", "keep its own surfaces aseptic")],
    "exploration-rover": [("rocker-bogie suspension", "climb rubble and crater rims"),
                          ("ground-penetrating radar", "map what lies underfoot"),
                          ("spectrometer payload", "read the chemistry of new ground")],
    "humanoid-companion": [("emotion-voice analyzer", "read moods and respond kindly"),
                           ("expressive faceplate", "hold warm, natural conversations"),
                           ("proximity skin", "accept a hug without flinching")],
    "aerial-drone": [("3-axis stabilized gimbal", "hold a rock-steady survey image"),
                     ("thermal imager", "find heat signatures in the dark"),
                     ("swarm-link radio", "fly coordinated patterns with its siblings")],
    "underwater-drone": [("vectored thruster set", "hold station in strong currents"),
                         ("water-chemistry probe", "sample the deep on the move"),
                         ("sonar array", "map wrecks and reefs in zero visibility")],
    "construction-rig": [("hydraulic excavator arm", "dig, lift, and place steel"),
                         ("site-survey lidar", "grade to the centimeter"),
                         ("proximity safety curtain", "work beside crews without risk")],
    "agricultural-bot": [("multispectral crop camera", "spot stress before eyes can"),
                         ("soft picking gripper", "harvest ripe fruit unbruised"),
                         ("precision sprayer boom", "treat only the plants that need it")],
    "security-sentinel": [("thermal night-vision ring", "see intruders in total darkness"),
                          ("gunshot-detection array", "pinpoint threats in seconds"),
                          ("patrol-dock network", "hand off coverage without gaps")],
}


def build_body(class_key, idx, seq):
    spec = CLASSES[class_key]
    name = spec["names"][idx]
    body_id = "JAH-BOT-%06d" % seq
    lo, hi = spec["height"]
    height = lo + h_int(body_id + ":h", hi - lo + 1)
    lo, hi = spec["mass"]
    mass = round(lo + h_int(body_id + ":m", hi - lo + 1) * (hi - lo) / max(1, hi - lo), 1)
    mass = lo + h_int(body_id + ":m", hi - lo + 1)
    lo, hi = spec["payload"]
    payload = lo + h_int(body_id + ":p", hi - lo + 1)
    materials = pick(body_id + ":mat", spec["materials"], k=2 + h_int(body_id + ":matk", 2))
    act_list = []
    for aname, dof in spec["actuators"]:
        if h_int(body_id + ":act:" + aname, 4) > 0 or len(act_list) < 2:
            act_list.append("%s (%d-DOF)" % (aname, dof))
    sensors = pick(body_id + ":sen", spec["sensors"], k=3 + h_int(body_id + ":senk", 3))
    power = spec["power"][h_int(body_id + ":pow", len(spec["power"]))]
    mobility = spec["mobility"][h_int(body_id + ":mob", len(spec["mobility"]))]
    tags = pick(body_id + ":tag", spec["tags"], k=4 + h_int(body_id + ":tagk", 3))
    feat, verb = FEATURE_VERB[class_key][h_int(body_id + ":feat", len(FEATURE_VERB[class_key]))]
    blurb = (spec["blurb1"].format(name=name) + " " +
             spec["blurb2"].format(name=name, feat=feat, verb=verb))
    compute, interfaces, operating_limits = build_systems(class_key, body_id)
    width_cm = round(height * (0.45 + h_int(body_id + ":w", 30) / 100.0), 1)
    depth_cm = round(height * (0.35 + h_int(body_id + ":d", 25) / 100.0), 1)
    return {
        "id": body_id,
        "name": name,
        "class": class_key,
        "height_cm": height,
        "width_cm": width_cm,
        "depth_cm": depth_cm,
        "mass_kg": mass,
        "materials": materials,
        "actuators": act_list,
        "sensors": sensors,
        "power": power,
        "compute": compute,
        "mobility": mobility,
        "payload_kg": payload,
        "interfaces": interfaces,
        "operating_limits": operating_limits,
        "tags": tags,
        "blurb": blurb,
        "svg_seed": int(hashlib.sha256(("svg" + body_id).encode()).hexdigest(), 16) % (2 ** 31),
    }


def main():
    bodies = []
    seq = 1
    for class_key in CLASSES:  # dict order = fixed class order
        for i in range(12):
            bodies.append(build_body(class_key, i, seq))
            seq += 1
    assert len(bodies) == 120
    ids = [b["id"] for b in bodies]
    assert len(set(ids)) == 120
    names = [b["name"] for b in bodies]
    assert len(set(names)) == 120, "body names must be unique"
    out = os.path.join(ROOT, "data", "bodies.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(bodies, f, separators=(",", ":"))
    print("wrote", out, len(bodies), "bodies")


if __name__ == "__main__":
    main()
