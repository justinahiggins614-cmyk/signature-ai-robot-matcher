#!/usr/bin/env node
/* Functional harness for the Signature AI to Robot Matcher.
 * Drives the REAL shipped page code (extracted verbatim from index.html)
 * inside a DOM stub, against the REAL shipped data files.
 * Usage: node code/qa/functional_harness.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const zlib = require("zlib");
const { Readable } = require("stream");

const ROOT = path.resolve(__dirname, "..", "..");

/* ---------------- DOM stub ---------------- */
function makeEl(tag, id) {
  const listeners = {};
  const children = [];
  const el = {
    tagName: (tag || "div").toUpperCase(), id: id || "",
    _html: "", style: {}, dataset: {}, disabled: false, value: "",
    textContent: "", title: "", src: "", href: "",
    classList: { _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); } },
    set innerHTML(v) { this._html = String(v); },
    get innerHTML() { return this._html; },
    addEventListener(t, f) { (listeners[t] = listeners[t] || []).push(f); },
    removeEventListener() {},
    appendChild(c) { children.push(c); return c; },
    remove() {}, scrollIntoView() {}, click() { if (typeof this.onclick === "function") this.onclick(); },
    pause() {}, play() { return Promise.reject(new Error("no audio in harness")); },
    getAttribute() { return null; }, setAttribute() {}, removeAttribute() {},
    querySelectorAll() { return []; }, querySelector() { return null; },
    scrollTop: 0, scrollHeight: 0,
    onclick: null, onend: null, onerror: null, onended: null,
    __fire(t, ev) { (listeners[t] || []).forEach(f => f.call(this, ev || { preventDefault() {} })); },
    __children: children,
  };
  return el;
}

const byId = {};
const qsel = {};
const docListeners = {};
const localStore = {};
const localStorage = {
  getItem: k => (k in localStore ? localStore[k] : null),
  setItem: (k, v) => { localStore[k] = String(v); },
  removeItem: k => { delete localStore[k]; },
  clear: () => { for (const k of Object.keys(localStore)) delete localStore[k]; },
};

const location = { hash: "#/", search: "", origin: "https://t", pathname: "/index.html",
  href: "https://t/index.html", reload() {} };
const navigator = { onLine: true, clipboard: { writeText: async t => { global.__copied = t; } } };
const document = {
  title: "",
  getElementById(id) { return byId[id] || (byId[id] = makeEl("div", id)); },
  querySelector(sel) { return qsel[sel] || (qsel[sel] = makeEl("div")); },
  querySelectorAll() { return []; },
  createElement(tag) { return makeEl(tag); },
  head: makeEl("head"), body: makeEl("body"),
  addEventListener(t, f) { (docListeners[t] = docListeners[t] || []).push(f); },
  removeEventListener() {},
  documentElement: makeEl("html"),
  __docFire(t, ev) { (docListeners[t] || []).forEach(f => f.call(document, ev || { preventDefault() {}, key: "" })); },
};
document.body.contains = () => false;
const window = { innerWidth: 1280, addEventListener() {}, scrollTo() {}, open() {},
  location, navigator, document };

/* fetch stub: serves real repo files over the virtual site root */
async function fetchStub(url) {
  const m = /^(?:https?:\/\/[^/]+\/[^/]+\/)?([^?#]*)/.exec(String(url));
  let p = (m && m[1]) || "";
  if (!p) p = "index.html";
  const fp = path.join(ROOT, p);
  if (!fs.existsSync(fp) || !fs.statSync(fp).isFile()) return { ok: false, status: 404 };
  const buf = fs.readFileSync(fp);
  return {
    ok: true, status: 200,
    body: Readable.toWeb(Readable.from([buf])),
    json: async () => JSON.parse(buf.toString("utf8")),
    text: async () => buf.toString("utf8"),
  };
}

const sandbox = {
  console, setTimeout, clearTimeout, setInterval, clearInterval,
  URLSearchParams, DecompressionStream, Response, ReadableStream, WritableStream,
  document, window, location, navigator, localStorage,
  fetch: fetchStub,
  addEventListener() {}, removeEventListener() {},
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

/* extract the 5 page script blocks verbatim + expose internals */
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const blocks = [...html.matchAll(/<script(?![^>]*json)>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (blocks.length !== 5) throw new Error("expected 5 page script blocks, got " + blocks.length);
const accessor = `
;globalThis.__T = {
  DB, MISSIONS, TOUR, TOUR_SEEN, TOUR_STEP,
  mixPair, cyrb, demoReply, fitBreakdown, pairText, pairExportJSON, pairCard,
  scoreDial, bodySVG, bodySpecText, getPair, getBody, getAI,
  vHome, vPairs, vBodies, vBody, vMix, vPair, finderGo, route, loadAll,
  paintCounter, arcCounts, speak, stopSpeak, togglePause, wirePair,
  bootErrorPanel, dataReady, fetchWithTimeout, tryFetchJSON,
  tourStart, tourEnd, tourNext, tourBack, tourShow, tourBoot,
  setAz: l => { azLetter = l; }, setAzPage: p => { azPage = p; },
  getAz: () => azLetter, getAzPage: () => azPage,
};`;
vm.runInContext(blocks.join("\n;\n") + accessor, sandbox, { filename: "index-scripts.js" });
const T = sandbox.__T;
const sdoc = sandbox.document;
const el = id => sdoc.getElementById(id);
const qel = sel => sdoc.querySelector(sel);

/* ---------------- test runner ---------------- */
const results = [];
const sleep = ms => new Promise(r => setTimeout(r, ms));
function ok(name, cond, extra) {
  results.push([cond ? "PASS" : "FAIL", name, cond ? "" : (extra || "")]);
  if (!cond) console.error("FAIL:", name, extra || "");
}
async function waitFor(fn, ms, what) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(50); }
  return false;
}

(async function main() {
  /* boot IIFE runs at parse; wait for it */
  ok("boot loads real index (17,000 rows)", await waitFor(() => T.DB.idx && T.DB.idx.length === 17000, 15000), "idx len=" + (T.DB.idx && T.DB.idx.length));
  ok("boot loads 120 bodies", T.DB.bodies && T.DB.bodies.length === 120, "len=" + (T.DB.bodies && T.DB.bodies.length));
  ok("boot loads 270 AIs", T.DB.pool && T.DB.pool.length === 270, "len=" + (T.DB.pool && T.DB.pool.length));
  ok("counter painted live to 17,000", el("paircount").textContent === "17,000", JSON.stringify(el("paircount").textContent));
  ok("boot status LIVE", el("bootstatus").textContent === "LIVE", JSON.stringify(el("bootstatus").textContent));
  ok("manifest is authoritative source", T.DB.manifestSrc === "matcher-manifest.json", T.DB.manifestSrc);
  T.tourEnd(); localStorage.clear();

  /* ---- exact pair resolution ---- */
  const p1 = await T.getPair("JAH-PAIR-000001");
  ok("getPair JAH-PAIR-000001 resolves", !!p1 && p1.id === "JAH-PAIR-000001");
  ok("pair has score 0..100", p1 && p1.score >= 0 && p1.score <= 100, "score=" + (p1 && p1.score));
  ok("pair has 3-part rationale", p1 && p1.rationale && p1.rationale.capability && p1.rationale.temperament && p1.rationale.task);
  ok("pair has 5 demo lines", p1 && p1.demo_lines && p1.demo_lines.length === 5);
  ok("pair ai_id resolves in pool", p1 && !!T.getAI(p1.ai_id));
  ok("pair body_id resolves in bodies", p1 && !!T.getBody(p1.body_id));
  const pLast = await T.getPair("JAH-PAIR-017000");
  ok("last pair JAH-PAIR-017000 resolves", !!pLast && pLast.id === "JAH-PAIR-017000");
  ok("unforged JAH-PAIR-017001 -> null", (await T.getPair("JAH-PAIR-017001")) === null);
  ok("malformed JAH-PAIR-ABC -> null", (await T.getPair("JAH-PAIR-ABC")) === null);

  /* ---- pair view ---- */
  location.search = "?pair=JAH-PAIR-000001"; T.route();
  ok("vPair renders real record", await waitFor(() => el("app").innerHTML.includes("JAH-PAIR-000001"), 8000));
  const ph = el("app").innerHTML;
  ok("pair view shows score dial 71", ph.includes(">71<"));
  ok("pair view shows rationale", ph.includes("Capability fit."));
  ok("pair view labels concept fit boundary", ph.includes("documented concept fit only"));
  ok("pair view carries SIMULATION badge", ph.includes("SIMULATION"));
  ok("pair view links methodology", ph.includes("methodology.html"));
  ok("pair view has read-aloud + downloads", ph.includes('id="rp"') && ph.includes('id="dpair"') && ph.includes('id="jpair"'));
  ok("pair view has shell-aware demo", ph.includes('id="din"') && ph.includes('id="dgo"'));
  ok("document title set for pair", document.title.includes("JAH-PAIR-000001"));
  location.search = "?pair=JAH-PAIR-999999"; T.route();
  ok("unforged pair -> not-forged message", await waitFor(() => el("app").innerHTML.includes("not forged yet"), 5000));
  location.search = "?pair=JAH-PAIR-XYZ"; T.route();
  ok("malformed pair id -> not-recognized message", await waitFor(() => el("app").innerHTML.includes("not a valid pair ID"), 5000));

  /* ---- random pair ---- */
  location.href = "https://t/index.html"; location.search = "";
  el("frand").onclick();
  const rm = /^\?pair=JAH-PAIR-(\d{6})$/.exec(location.href);
  ok("random button navigates to ?pair=JAH-PAIR-######", !!rm, location.href);
  const rn = rm ? +rm[1] : 0;
  ok("random id in 1..17000", rn >= 1 && rn <= 17000, String(rn));
  const pr = await T.getPair("JAH-PAIR-" + String(rn).padStart(6, "0"));
  ok("random pair resolves to a REAL record", !!pr && pr.id === "JAH-PAIR-" + String(rn).padStart(6, "0"));

  /* ---- finder ---- */
  location.href = "https://t/index.html";
  el("fq").value = "bakery";
  el("fgo").onclick();
  ok("finder returns results for 'bakery'", await waitFor(() => el("fhits").innerHTML.includes("JAH-PAIR-"), 3000), el("fhits").innerHTML.slice(0, 120));
  el("fq").value = "zxqwq";
  el("fgo").onclick();
  ok("finder no-result -> explicit empty state", await waitFor(() => el("fhits").innerHTML.includes("No archived pair matches"), 3000));
  el("fq").value = "";
  el("fgo").onclick();
  ok("finder empty query -> guidance", await waitFor(() => el("fhits").innerHTML.includes("Describe what you need"), 3000));
  el("fq").value = "JAH-PAIR-000123";
  el("fgo").onclick();
  ok("finder exact ID jumps to record", location.href === "?pair=JAH-PAIR-000123", location.href);

  /* ---- pairs A-Z + pagination + filter ---- */
  location.search = ""; location.hash = "#/pairs"; location.href = "https://t/index.html";
  T.setAz("A"); T.setAzPage(0); T.route();
  ok("pairs A-Z renders", el("app").innerHTML.includes("Pairs A–Z"));
  ok("pairs A-Z shows letter tabs", el("app").innerHTML.includes('data-az="B"'));
  ok("pairs A-Z shows pagination", /Page 1 of \d+/.test(el("app").innerHTML), (el("app").innerHTML.match(/Page \d+ of \d+/) || [])[0]);
  const rowsA = T.DB.idx.filter(r => r[1][0].toUpperCase() === "A").length;
  ok("pairs A-Z page 1 holds 24 cards", (el("app").innerHTML.match(/Open pair →/g) || []).length === Math.min(24, rowsA));
  T.setAzPage(1); T.vPairs();
  ok("pagination advances to page 2", /Page 2 of \d+/.test(el("app").innerHTML));
  T.setAzPage(0); T.vPairs();
  el("pfq").value = "warehouse";
  el("pfq").__fire("input");
  ok("pair filter finds matches", await waitFor(() => el("pfhits").innerHTML.includes("match"), 3000));
  el("pfq").value = "zxqwq";
  el("pfq").__fire("input");
  ok("pair filter no-result -> explicit empty state", await waitFor(() => el("pfhits").innerHTML.includes(">0</b> matches"), 3000));
  el("pfq").value = "JAH-PAIR-000777";
  el("pfq").__fire("input");
  ok("pair filter full ID jumps to record", await waitFor(() => location.href === "?pair=JAH-PAIR-000777", 3000), location.href);

  /* ---- bodies ---- */
  location.search = ""; location.hash = "#/bodies"; location.href = "https://t/index.html"; T.route();
  ok("bodies view renders 120", el("app").innerHTML.includes("120 bodies"));
  ok("bodies view links body pages", el("app").innerHTML.includes("?body=JAH-BOT-000001"));
  location.search = "?body=JAH-BOT-000001"; T.route();
  ok("body page renders full specs", await waitFor(() => el("app").innerHTML.includes("Full specification"), 3000));
  ok("body page shows Hearthward", el("app").innerHTML.includes("Hearthward"));
  location.search = "?body=JAH-BOT-999999"; T.route();
  ok("unknown body -> not found", await waitFor(() => el("app").innerHTML.includes("Body not found"), 3000));
  location.search = "?body=NOPE"; T.route();
  ok("malformed body id -> not recognized", await waitFor(() => el("app").innerHTML.includes("not a valid body ID"), 3000));
  /* body + #/mix combo preselects the body */
  location.search = "?body=JAH-BOT-000003"; location.hash = "#/mix"; T.route();
  ok("body+mix preselects body in Mix Lab", el("mbody") && String(el("mbody").value) === "2", String(el("mbody") && el("mbody").value));

  /* ---- mix lab ---- */
  location.search = ""; location.hash = "#/mix"; T.route();
  ok("mix lab renders", el("app").innerHTML.includes("Mix Lab"));
  const ai0 = T.DB.pool[0], b0 = T.DB.bodies[0];
  el("mai").value = ai0.name; el("mbody").value = "0"; el("mmis").value = T.MISSIONS[0];
  el("mforge").onclick();
  ok("mix lab forges a custom pair", await waitFor(() => el("mout").innerHTML.includes("JAH-MIX-"), 3000));
  const mout = el("mout").innerHTML;
  ok("forged pair shows score + rationale", mout.includes("Capability fit.") && mout.includes("USER CREATED"));
  ok("forged pair offers copy/download/read", mout.includes('id="mcp"') && mout.includes('id="mdj"') && mout.includes('id="mrd"'));
  const mx1 = T.mixPair(ai0, b0, T.MISSIONS[0]);
  const mx2 = T.mixPair(ai0, b0, T.MISSIONS[0]);
  ok("mixPair is deterministic", JSON.stringify(mx1) === JSON.stringify(mx2));
  ok("mixPair id shape JAH-MIX-XXXXXX", /^JAH-MIX-[0-9A-F]{6}$/.test(mx1.id), mx1.id);
  ok("mixPair score in range", mx1.score >= 0 && mx1.score <= 100);
  ok("mixPair rationale complete", !!(mx1.rationale.capability && mx1.rationale.temperament && mx1.rationale.task));
  el("mai").value = "no such ai xyz";
  el("mforge").onclick();
  ok("mix lab unknown AI -> toast, no crash", await waitFor(() => el("floatbar").style.display === "block", 3000));

  /* ---- demo reply engine (real shipped function) ---- */
  const dai = T.getAI(p1.ai_id), db = T.getBody(p1.body_id);
  let r = T.demoReply("what is your mission?", p1, db, dai, 0);
  ok("demo answers mission", r.text.includes(p1.mission), r.text.slice(0, 80));
  r = T.demoReply("what is the match score?", p1, db, dai, 0);
  ok("demo answers score", r.text.includes(String(p1.score)));
  r = T.demoReply("describe your body", p1, db, dai, 0);
  ok("demo answers body", r.text.includes(p1.body_name));
  r = T.demoReply("what sensors do you have?", p1, db, dai, 0);
  ok("demo answers sensors", r.text.includes(db.sensors[0]));
  r = T.demoReply("how is your battery?", p1, db, dai, 0);
  ok("demo answers power", r.text.toLowerCase().includes("battery") || r.text.includes("48V"));
  r = T.demoReply("blorple snarf", p1, db, dai, 0);
  ok("demo fallback cycles demo_lines[0]", r.text === p1.demo_lines[0] && r.li === 1);
  r = T.demoReply("blorple snarf", p1, db, dai, r.li);
  ok("demo fallback advances line index", r.text === p1.demo_lines[1] && r.li === 2);

  /* ---- score / rationale math ---- */
  const fb = T.fitBreakdown(p1, db, dai);
  const overlap = dai.tags.filter(t => db.tags.includes(t));
  const union = [...new Set([...dai.tags, ...db.tags])];
  const bonus = Math.round(25 * (overlap.length / Math.max(1, union.length)));
  ok("breakdown shows score math", fb.includes("Match score " + p1.score + "/100") && fb.includes("capability-overlap bonus " + bonus));
  ok("breakdown shows shared tags", fb.includes("Shared capabilities (" + overlap.length + ")"));
  ok("breakdown links methodology", fb.includes("methodology.html"));
  const sd = T.scoreDial(71);
  ok("scoreDial renders 71", sd.includes(">71<") && sd.includes("<svg"));
  const svg = T.bodySVG(db, 150);
  ok("bodySVG renders body art", svg.includes("<svg") && svg.includes(db.name) && svg.includes(db.id));

  /* ---- speech tiers ---- */
  T.speak("Hello world.");
  ok("speak shows floating bar, no throw", el("floatbar").style.display === "block");
  ok("speak chain terminates on dead tiers", await waitFor(() => el("floatbar").style.display === "none", 5000));
  window.speechSynthesis = { speak(u) { setTimeout(() => u.onend && u.onend(), 5); }, cancel() {}, pause() {}, resume() {} };
  T.speak("Hi there.");
  ok("speechSynthesis tier used when present", await waitFor(() => el("floatbar").style.display === "none", 5000));
  delete window.speechSynthesis;

  /* ---- fetch timeout ---- */
  const realFetch = sandbox.fetch;
  sandbox.fetch = () => new Promise(() => {});
  let timedOut = false;
  try { await T.fetchWithTimeout("data/index/pairs.idx.json.gz", 50); }
  catch (e) { timedOut = /timeout after 50ms/.test(e.message); }
  ok("fetchWithTimeout aborts at deadline", timedOut);
  sandbox.fetch = realFetch;

  /* ---- error states ---- */
  ok("bootErrorPanel offers reload", T.bootErrorPanel().includes("Reload index"));
  ok("dataReady true when loaded", T.dataReady() === true);

  /* ---- tour + guide ---- */
  ok("tour has 10 steps", T.TOUR.length === 10, String(T.TOUR.length));
  T.tourEnd(); localStorage.clear();
  T.tourStart(0);
  ok("tour starts at step 1", el("jah-tour").hidden === false && el("jah-tour-k").textContent.includes("STEP 1 OF 10"));
  T.tourNext();
  ok("tour step 2 highlights finder", qel("#fq").classList.contains("jah-tour-hl"));
  for (let i = 0; i < 5; i++) T.tourNext();
  ok("tour reaches nav step", el("jah-tour-t").textContent.includes("Pair records"));
  ok("nav step button says Continue", el("jah-tour-next").textContent.includes("Continue"));
  T.tourNext();
  ok("nav step goes to a real pair", location.href === "?pair=JAH-PAIR-000001", location.href);
  ok("nav step stores resume index", localStorage.getItem(T.TOUR_STEP) === "7", localStorage.getItem(T.TOUR_STEP));
  location.search = "?pair=JAH-PAIR-000001";
  T.tourBoot();
  ok("tour resumes at step 8 on pair page", el("jah-tour-k").textContent.includes("STEP 8 OF 10"), el("jah-tour-k").textContent);
  ok("resume highlights demo input", qel("#din").classList.contains("jah-tour-hl"));
  T.tourNext();
  ok("step 9 highlights read-aloud", qel("#rp").classList.contains("jah-tour-hl"));
  T.tourNext();
  ok("step 10 highlights guide button", qel("#jah-guide-btn").classList.contains("jah-tour-hl"));
  T.tourNext();
  ok("tour ends and marks seen", el("jah-tour").hidden === true && localStorage.getItem(T.TOUR_SEEN) === "1");
  T.tourStart(0);
  document.__docFire("keydown", { key: "Escape", preventDefault() {} });
  ok("Esc ends tour", el("jah-tour").hidden === true);
  el("jah-guide-btn").onclick();
  ok("guide panel opens", el("jah-guide").hidden === false);
  ok("guide documents features (static HTML verified)", html.includes("How to use the AI to Robot Matcher") && html.includes("Mix Lab") && html.includes("Shell-aware demo") && html.includes("Read aloud") && html.includes("tiered speech") && html.includes("concept fit"));
  el("jah-guide-close").onclick();
  ok("guide panel closes", el("jah-guide").hidden === true);

  /* ---- remaining routes ---- */
  location.search = ""; location.hash = "#/"; location.href = "https://t/index.html"; T.route();
  ok("home route renders explainer + featured", el("app").innerHTML.includes("How matching works"));
  ok("home shows live body/AI counts", el("app").innerHTML.includes("120 robot bodies") && el("app").innerHTML.includes("270 Signature AIs"));

  console.log("\n==== RESULTS ====");
  let fails = 0;
  for (const [s, n, x] of results) { if (s === "FAIL") fails++; }
  console.log(results.filter(r => r[0] === "PASS").length + " passed, " + fails + " failed, " + results.length + " total");
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error("HARNESS CRASH:", e); process.exit(2); });
