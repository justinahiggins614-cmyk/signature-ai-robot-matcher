#!/usr/bin/env python3
"""Build the unified A-Z pair archive (browse.html) + per-letter lazy data files.

  browse.html              -> full pair catalog as A-Z collapsible <details> lists;
                              each letter section lazy-loads data/index/az/<L>.json.gz
                              on first open (nothing is fetched at page boot)
  data/index/az/<L>.json.gz -> compact rows [id, ai_name, body_name, mission, chunk]

Rebuilt by the pair drip after every run, AFTER the index rebuild, so the
stamped counts are never one run behind. Fails loudly on any integrity problem.
"""
import gzip
import html as htmlmod
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = (
    ":root{--bg:#0d1117;--panel:#141b26;--line:#2a3444;--amber:#ffcf6e;--ink:#e8edf4;--dim:#9aa6ba}"
    "body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}"
    ".w{max-width:1100px;margin:0 auto;padding:16px}"
    "h1{color:var(--amber);font-size:26px;margin:14px 0 6px}"
    "a{color:var(--amber)}"
    ".sub{color:var(--dim);font-size:15px;margin:0 0 14px}"
    ".countline{font-size:17px;margin:10px 0 16px}"
    ".countline b{color:var(--amber);font-size:20px}"
    ".searchbar{display:flex;gap:8px;margin:14px 0;flex-wrap:wrap}"
    ".searchbar input{flex:1;min-width:220px;min-height:44px;background:#0a0e14;border:1px solid var(--line);border-radius:10px;color:var(--ink);padding:10px 14px;font-size:15px}"
    ".btn{display:inline-block;background:var(--amber);color:#0a0e14;font-weight:700;border:0;border-radius:10px;padding:10px 18px;font-size:15px;cursor:pointer;text-decoration:none;margin:4px 6px 4px 0;min-height:44px}"
    ".btn.sm{font-size:13px;padding:8px 14px}"
    ".btn.ghost{background:transparent;color:var(--amber);border:1px solid var(--amber)}"
    ".pill{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:20px;padding:2px 10px;color:var(--dim);margin:2px 4px 2px 0}"
    ".pill.gen{color:#7ee2a8;border-color:#2f5b40}"
    "details.az{border:1px solid var(--line);border-radius:12px;margin:8px 0;background:var(--panel)}"
    "details.az>summary{cursor:pointer;padding:14px 16px;font-size:17px;font-weight:700;color:var(--amber);list-style:none;display:flex;justify-content:space-between;align-items:center;min-height:44px}"
    "details.az>summary::-webkit-details-marker{display:none}"
    "details.az>summary .n{font-size:13px;color:var(--dim);font-weight:400}"
    "details.az .body{padding:0 16px 16px}"
    ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}"
    ".card{background:#0a0e14;border:1px solid var(--line);border-radius:14px;padding:14px;margin:0}"
    ".card h3{margin:0 0 8px;font-size:15px;color:var(--ink);word-break:break-word}"
    ".card h3 .bid{color:var(--amber)}"
    ".card .btn.sm{margin-top:10px}"
    ".loading{color:var(--dim);padding:12px 0}"
    ".nav{margin:14px 0;display:flex;flex-wrap:wrap;gap:10px}"
    "footer{color:var(--dim);font-size:13px;margin:26px 0 10px;text-align:center}"
)

JS = r"""
"use strict";
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
var cache={};
function card(r){
 return '<div class="card"><h3><span class="bid">'+esc(r[0])+'</span> &middot; '+esc(r[2])+'</h3>'
 +'<div><span class="pill gen">GENERATED</span><span class="pill">&#129302; '+esc(r[1])+'</span>'
 +'<span class="pill">&#129470; '+esc(r[2])+'</span><span class="pill">&#127919; '+esc(r[3])+'</span></div>'
 +'<a class="btn sm" href="?pair='+esc(r[0])+'">Open pair &rarr;</a></div>';
}
function loadLetter(L,box,done){
 if(cache[L]){box.innerHTML='<div class="grid">'+cache[L].map(card).join("")+"</div>";if(done)done();return;}
 box.innerHTML='<p class="loading">Loading letter '+esc(L)+'&hellip;</p>';
 fetch("data/index/az/"+L+".json.gz").then(function(resp){
  if(!resp.ok)throw new Error("HTTP "+resp.status);
  return resp.arrayBuffer();
 }).then(function(buf){
  var ds=new DecompressionStream("gzip");
  var stream=new Response(new Blob([buf]).stream().pipeThrough(ds)).json();
  return stream;
 }).then(function(rows){
  cache[L]=rows;
  box.innerHTML='<div class="grid">'+rows.map(card).join("")+"</div>";
  if(done)done();
 }).catch(function(e){
  box.innerHTML='<p class="loading">Could not load letter '+esc(L)+'. <a href="./">Back to the matcher</a></p>';
 });
}
document.querySelectorAll("details.az").forEach(function(d){
 var L=d.getAttribute("data-l"),box=d.querySelector(".body"),loaded=false;
 d.addEventListener("toggle",function(){
  if(d.open&&!loaded){loaded=true;loadLetter(L,box);}
 });
});
var sq=document.getElementById("q"),sgo=document.getElementById("go"),
    sx=document.getElementById("cx"),hits=document.getElementById("hits");
function clearSearch(){sq.value="";hits.innerHTML="";sx.style.display="none";
 document.querySelectorAll("details.az").forEach(function(d){d.style.display="";});}
sx.onclick=clearSearch;
function doSearch(){
 var raw=sq.value.trim();if(!raw){clearSearch();return;}
 var m=/JAH-PAIR-\d{6}/i.exec(raw);
 if(m){location.href="?pair="+encodeURIComponent(m[0].toUpperCase());return;}
 var q=raw.toLowerCase();
 hits.innerHTML='<p class="loading">Searching the full archive&hellip;</p>';
 sx.style.display="";
 var letters=[].map.call(document.querySelectorAll("details.az"),function(d){return d.getAttribute("data-l");});
 var pending=letters.map(function(L){
  if(cache[L])return Promise.resolve(cache[L]);
  return fetch("data/index/az/"+L+".json.gz").then(function(r){if(!r.ok)throw 0;return r.arrayBuffer();})
   .then(function(b){return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream("gzip"))).json();})
   .then(function(rows){cache[L]=rows;return rows;})
   .catch(function(){return[];});
 });
 Promise.all(pending).then(function(all){
  var out=[];
  all.forEach(function(rows){rows.forEach(function(r){
   if((r[0]+" "+r[1]+" "+r[2]+" "+r[3]).toLowerCase().indexOf(q)>=0)out.push(r);
  });});
  out=out.slice(0,48);
  document.querySelectorAll("details.az").forEach(function(d){d.style.display="none";});
  hits.innerHTML="<p><b>"+out.length+"</b> match"+(out.length===1?"":"es")+" for &ldquo;"+esc(raw)+"&rdquo;"
   +(out.length===48?" (first 48 shown &mdash; refine your search)":"")+"</p>"
   +'<div class="grid">'+out.map(card).join("")+"</div>";
 });
}
sgo.onclick=doSearch;
sq.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();doSearch();}});
"""


def main():
    idx_path = os.path.join(ROOT, "data/index/pairs.idx.json.gz")
    state_path = os.path.join(ROOT, "data/state.json")
    rows = json.load(gzip.open(idx_path, "rt", encoding="utf-8"))
    next_index = json.load(open(state_path))["next_index"]
    total = next_index - 1

    # ---- fail-loud integrity assertions ----
    assert len(rows) == total, "idx rows=%d but next_index-1=%d" % (len(rows), total)
    ids = [r[0] for r in rows]
    assert len(set(ids)) == len(ids), "duplicate pair ids in index"
    nums = sorted(int(i.rsplit("-", 1)[1]) for i in ids)
    assert nums == list(range(1, total + 1)), "pair ids not contiguous 1..%d" % total

    buckets = {}
    for r in rows:
        ch = (r[1] or "?")[0].upper()
        L = ch if ("A" <= ch <= "Z") else "#"
        buckets.setdefault(L, []).append(r)
    assert sum(len(v) for v in buckets.values()) == total, "letter buckets do not cover all rows"

    az_dir = os.path.join(ROOT, "data/index/az")
    os.makedirs(az_dir, exist_ok=True)
    letters = sorted(buckets)
    for L in letters:
        blob = json.dumps(buckets[L], separators=(",", ":")).encode("utf-8")
        with gzip.GzipFile(os.path.join(az_dir, "%s.json.gz" % L), "wb", mtime=0) as f:
            f.write(blob)

    det = []
    for L in letters:
        c = len(buckets[L])
        det.append(
            '<details class="az" data-l="%s"><summary><span>%s</span>'
            '<span class="n">%s pair%s</span></summary>'
            '<div class="body"><p class="loading">Open to load this letter&rsquo;s pairs.</p></div></details>'
            % (htmlmod.escape(L), htmlmod.escape(L), f"{c:,}", "" if c == 1 else "s"))

    page = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Pair archive A&ndash;Z | The Signature AI Robot Matcher</title>"
            "<meta name=\"description\" content=\"The full A-Z archive of documented best-match pairs "
            "of Signature AIs and Signature robot bodies.\">"
            "<style>" + CSS + "</style></head><body><div class=\"w\">"
            "<div class=\"nav\"><a href=\"./\">&larr; The matcher</a><a href=\"pairs-index.html\">Static tables</a></div>"
            "<h1>&#129302; Pair archive A&ndash;Z</h1>"
            "<p class=\"sub\">Every documented best-match pairing of a Signature AI with its Signature "
            "robot body &mdash; each with a match score, a written best-fit rationale, and a live demo "
            "where the AI speaks aware of its own body. Open a letter to browse; nothing loads until you do.</p>"
            "<p class=\"countline\"><b>%s</b> documented pairs, marching to 1,000,000.</p>"
            "<div class=\"searchbar\"><input id=\"q\" type=\"text\" placeholder=\"Search the archive &mdash; pair ID, AI, body, or mission&hellip;\" "
            "aria-label=\"Search the pair archive\">"
            "<button class=\"btn\" id=\"go\">Search</button>"
            "<button class=\"btn ghost\" id=\"cx\" style=\"display:none\">&#10005; Clear</button></div>"
            "<div id=\"hits\"></div>"
            "%s"
            "<footer>The Signature AI Robot Matcher &middot; <a href=\"./\">matcher home</a> &middot; "
            "<a href=\"methodology.html\">methodology</a></footer>"
            "</div><script>" + JS + "</script></body></html>") % (f"{total:,}", "\n".join(det))

    out_path = os.path.join(ROOT, "browse.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)

    # fail-loud: the stamped count must be present and correct
    stamped = open(out_path, encoding="utf-8").read()
    want = "<b>%s</b> documented pairs" % f"{total:,}"
    assert want in stamped, "browse.html count stamp missing: %r" % want
    assert len(re.findall(r'details class="az"', stamped)) == len(letters), "letter section count mismatch"
    print("browse.html: %d letters, %s pairs stamped; data/index/az/*.json.gz written" % (len(letters), f"{total:,}"))


if __name__ == "__main__":
    main()
