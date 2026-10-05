#!/usr/bin/env python3
"""Build static bot-friendly HTML tables of all pairs (1000 per page) plus an index page.

Pre-rendered for lightweight crawlers that cannot run the JS app:
  pairs-index.html        -> links every static table page
  pairs-static-N.html     -> one table row per pair: pair ID, AI, body, class, mission, score
Rebuilt by the pair drip after every run.
"""
import gzip
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/"
PAGE_SIZE = 1000

CSS = ("body{margin:0;background:#0d1117;color:#e8edf4;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}"
       ".w{max-width:1100px;margin:0 auto;padding:16px}"
       "h1{color:#ffcf6e}a{color:#ffcf6e}"
       "table{width:100%;border-collapse:collapse;font-size:14px}"
       "th,td{border:1px solid #2a3444;padding:7px 10px;text-align:left;vertical-align:top}"
       "th{background:#0a0e14;color:#ffcf6e}"
       ".nav{margin:14px 0}.nav a{margin-right:10px}"
       ".jtabbar{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;-webkit-overflow-scrolling:touch;"
       "scrollbar-width:thin;border-bottom:1px solid rgba(128,128,128,.25)}"
       ".jtabbar a.jtab{flex:0 0 auto;text-decoration:none;border:1px solid rgba(160,160,160,.45);"
       "border-radius:999px;padding:9px 16px;font-size:.92em;color:inherit;background:rgba(127,127,127,.08);"
       "white-space:nowrap;font-family:inherit}"
       ".jtabbar a.jtab.on{background:#f5c518;border-color:#f5c518;color:#191919;font-weight:700}"
       ".jahnet{display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:center;"
       "font-size:12px;margin:22px 8px 10px}"
       ".jahnet .t{color:#9aa7ba;font-weight:700;letter-spacing:1px;margin-right:6px}"
       ".jahnet a{color:#9aa7ba;text-decoration:none;padding:3px 8px;border:1px solid #2a3444;border-radius:20px}"
       ".jahnet a:hover{color:#ffcf6e;border-color:#f5a623}"
       ".jahnet span.here{color:#0a0e14;background:#f5a623;border-color:#f5a623;font-weight:700;"
       "padding:3px 8px;border-radius:20px}"
       ".jahnet a.soon{opacity:.55;border-style:dashed}")

HEAD = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>{t} | The Signature AI Robot Matcher</title>"
        "<style>" + CSS + "</style></head><body><div class=\"w\">")


# --- NAV SWEEP (2026-10-04): pill tab bar + THE JAH NETWORK block, one nav
#     instance per page, nav at the bottom. Same content/behavior as index.html.
def tabbar(active):
    def cls(k):
        return " on" if k == active else ""
    return ("""<!-- JAH TAB BAR — pill tab bar, Manon's 2026-10-04 order (calculator screenshot as spec). -->
<style>
.jtabbar{display:flex;gap:8px;overflow-x:auto;padding:10px 12px;-webkit-overflow-scrolling:touch;scrollbar-width:thin;border-bottom:1px solid rgba(128,128,128,.25)}
.jtabbar a.jtab{flex:0 0 auto;text-decoration:none;border:1px solid rgba(160,160,160,.45);border-radius:999px;padding:9px 16px;font-size:.92em;color:inherit;background:rgba(127,127,127,.08);white-space:nowrap;font-family:inherit}
.jtabbar a.jtab.on{background:#f5c518;border-color:#f5c518;color:#191919;font-weight:700}
</style>
<nav class="jtabbar" aria-label="Site sections">
<a class="jtab%s" href="index.html">🏠 Front Door</a>
<a class="jtab%s" href="browse.html">📚 1 Million Archive</a>
<a class="jtab%s" href="methodology.html">Methodology</a><a class="jtab%s" href="pairs-index.html">Pairs Index</a>
</nav>
""" % (cls("index"), cls("browse"), cls("methodology"), cls("pairs-index")))


NAV_HTML = ('<nav class="jahnet" id="jahnet2" aria-label="JAH Network Global Ecosystem" '
            'role="navigation"></nav>')
NAV_JS = r"""<script>
"use strict";
/* ============ JAH NETWORK NAV (bottom, one instance per page) ============ */
const SITES = [
["signature-math","Signature Math"],["jah-calculator","Signature Universal Paradox Immune Calculator"],
["jah-dictionary","The Signature Dictionary"],["jah-wiki","JAH Wiki"],["jah-n-wiki-leaks","JAH-N Wiki Leaks"],
["signature-llama","Signature Llama: The Fully Cyber Utilizable AI"],["jah-ai-models","The Signature AI Phone Book"],
["cyber-patent-catalog","Globally Rejustered Patent Catalog"],["signature-one-archive/specs.html","Signature Spec Catalog Pending Patents"],
["jah-computer-systems","The Signature PC System Depository"],["signature-books","The Signature Book Depository"],
["signature-comics","The Signature Comic Store"],["signature-newspapers","The Signature Global Newspaper Archive"],
["signature-backend","The Signature AI Mix and Match Generator"],
["signature-boundless-generators","The Signature Boundless Generator Archive"],
["signature-ai-mixlab","The Signature AI Mix Lab"],["signature-ai-olypics","AI Olympics"],
["signature-chip-maker","The Signature Computer Chip Maker and Archive"],["signature-app-archive","The Signature App Archive"],
["signature-ai-robot-matcher","The Signature AI Robot Matcher"],["signature-experiment-solver","The Signature Experiment Solver"],
["signature-ai-image-video-maker","Signature AI Pixel"],["signature-ai-song-maker","Signature Music Studio"],
["signature-fixit","The Signature Mr Fix-It"],["signature-university","The Signature University"],
["signature-cyber-mega-mall","The Signature Cyber Mega-Mall"],["signature-3d-print","The Signature 3D Print Mega Mall"],["signature-earth","Signature Earth"],["signature-flight-school","The Signature Flight School"],["signature-game-store","The Signature Game Store"],["signature-website-creator","The Signature Website Creator"],["signature-antivirus","The Signature Antivirus"],["signature-os-updater","The Signature OS Updater"],["signature-space-mapping","Signature Space Mapping"],["signature-cookbook","The Signature Cookbook"]];
const LIVE18={"signature-ai-mixlab":true,"signature-ai-olypics":true,"signature-chip-maker":true,"signature-app-archive":true,"signature-ai-robot-matcher":true,"signature-experiment-solver":true,"signature-ai-image-video-maker":true,"signature-ai-video-maker":true,"signature-ai-song-maker":true,"signature-math":true,"signature-fixit":true,"signature-earth":true,"signature-flight-school":true,"signature-game-store":true,"signature-website-creator":true,"signature-antivirus":true,"signature-os-updater":true,"signature-space-mapping":true,"signature-cookbook":true};
/* Site label renders dynamically from JAH-NETWORK-MANIFEST.json (site_count handled); static text stays as fallback. */
let netLabel='SITE 20 OF 33 · AI Robot Matcher ★ YOU ARE HERE';
function netPaint(){document.querySelectorAll('#jahnet2 a.here').forEach(function(a){a.textContent=netLabel;});}
fetch('JAH-NETWORK-MANIFEST.json').then(function(r){return r.ok?r.json():null;}).then(function(m){
 if(m&&m.site_number){const sc=m.site_count||SITES.length;
  let nm='AI Robot Matcher';
  if(m.official_name)nm=m.official_name.replace(/^The Signature /,'');
  netLabel='SITE '+m.site_number+' OF '+sc+' · '+nm+' ★ YOU ARE HERE';netPaint();}
}).catch(function(){});
function navHTML(){
 let h='<span class="t">THE JAH NETWORK</span>';
 SITES.forEach((s,i)=>{const n=i+1;
  if(n===20){return;}
  const soon=(n>=18&&!LIVE18[s[0]]);
  h+='<a class="'+(soon?'soon':'')+'" href="https://justinahiggins614-cmyk.github.io/'+s[0]+'/">'+n+' '+s[1]+(soon?' (soon)':'')+'</a>';});
 h+='<span class="here" aria-current="page">20 The Signature AI Robot Matcher \u2014 YOU ARE HERE</span>';
 return h;}
document.getElementById('jahnet2').innerHTML=navHTML();
/* sibling liveness verified server-side at push time; "(soon)" badge marks not-yet-live */
</script>
"""


def main():
    bodies = {b["id"]: b for b in json.load(open(os.path.join(ROOT, "data/bodies.json")))}
    pairs = []
    n = 1
    while True:
        path = os.path.join(ROOT, "data/pairs/pairs-c%05d.jsonl.gz" % n)
        if not os.path.exists(path):
            break
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                pairs.append(json.loads(line))
        n += 1

    pages = (len(pairs) + PAGE_SIZE - 1) // PAGE_SIZE
    idx = HEAD.replace("{t}", "Pair tables") + "<h1>The Signature AI Robot Matcher — static pair tables</h1>"
    idx += ("<p>" + str(len(pairs)) + " documented best-match pairs of Signature AIs and "
            "Signature robot bodies, marching to 1,000,000. Pre-rendered static tables for "
            "bots and scrapers.</p>" + tabbar("pairs-index") + "<div class=\"nav\">")
    for pg in range(1, pages + 1):
        lo = (pg - 1) * PAGE_SIZE + 1
        hi = min(pg * PAGE_SIZE, len(pairs))
        idx += "<a href=\"pairs-static-%d.html\">Pairs %d–%d</a>" % (pg, lo, hi)
    idx += ("</div><p><a href=\"./\">Back to the matcher →</a></p>"
            + NAV_HTML + NAV_JS + "</div></body></html>")
    with open(os.path.join(ROOT, "pairs-index.html"), "w", encoding="utf-8") as f:
        f.write(idx)

    for pg in range(1, pages + 1):
        seg = pairs[(pg - 1) * PAGE_SIZE:pg * PAGE_SIZE]
        h = HEAD.replace("{t}", "Pairs %d–%d" % ((pg - 1) * PAGE_SIZE + 1, (pg - 1) * PAGE_SIZE + len(seg)))
        h += "<h1>Robot pairs %d–%d</h1>" % ((pg - 1) * PAGE_SIZE + 1, (pg - 1) * PAGE_SIZE + len(seg))
        h += tabbar("pairs-index")
        h += ("<div class=\"nav\"><a href=\"pairs-index.html\">All tables</a>"
              + ("<a href=\"pairs-static-%d.html\">← prev</a>" % (pg - 1) if pg > 1 else "")
              + ("<a href=\"pairs-static-%d.html\">next →</a>" % (pg + 1) if pg < pages else "")
              + "<a href=\"./\">Back to the matcher →</a></div>")
        h += ("<table><tr><th>Pair ID</th><th>AI</th><th>Robot body</th>"
              "<th>Body class</th><th>Mission</th><th>Score</th></tr>")
        for p in seg:
            b = bodies.get(p["body_id"], {})
            h += ("<tr><td><a href=\"?pair=" + html.escape(p["id"]) + "\">" + html.escape(p["id"]) + "</a></td>"
                  "<td>" + html.escape(p["ai_name"]) + " <i>(" + html.escape(p["ai_id"]) + ")</i></td>"
                  "<td>" + html.escape(p["body_name"]) + " <i>(" + html.escape(p["body_id"]) + ")</i></td>"
                  "<td>" + html.escape(b.get("class", "")) + "</td>"
                  "<td>" + html.escape(p["mission"]) + "</td>"
                  "<td>" + str(p["score"]) + "/100</td></tr>")
        h += "</table>" + NAV_HTML + NAV_JS + "</div></body></html>"
        with open(os.path.join(ROOT, "pairs-static-%d.html" % pg), "w", encoding="utf-8") as f:
            f.write(h)
    print("pairs-index.html + %d static pages (%d pairs)" % (pages, len(pairs)))


if __name__ == "__main__":
    main()
