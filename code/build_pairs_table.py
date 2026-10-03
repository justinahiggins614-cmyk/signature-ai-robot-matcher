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
       ".nav{margin:14px 0}.nav a{margin-right:10px}")

HEAD = ("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>{t} | The Signature AI Robot Matcher</title>"
        "<style>" + CSS + "</style></head><body><div class=\"w\">")


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
    idx = HEAD.format(t="Pair tables") + "<h1>The Signature AI Robot Matcher — static pair tables</h1>"
    idx += ("<p>" + str(len(pairs)) + " documented best-match pairs of Signature AIs and "
            "Signature robot bodies, marching to 1,000,000. Pre-rendered static tables for "
            "bots and scrapers.</p><div class=\"nav\">")
    for pg in range(1, pages + 1):
        lo = (pg - 1) * PAGE_SIZE + 1
        hi = min(pg * PAGE_SIZE, len(pairs))
        idx += "<a href=\"pairs-static-%d.html\">Pairs %d–%d</a>" % (pg, lo, hi)
    idx += "</div><p><a href=\"./\">Back to the matcher →</a></p></div></body></html>"
    with open(os.path.join(ROOT, "pairs-index.html"), "w", encoding="utf-8") as f:
        f.write(idx)

    for pg in range(1, pages + 1):
        seg = pairs[(pg - 1) * PAGE_SIZE:pg * PAGE_SIZE]
        h = HEAD.format(t="Pairs %d–%d" % ((pg - 1) * PAGE_SIZE + 1, (pg - 1) * PAGE_SIZE + len(seg)))
        h += "<h1>Robot pairs %d–%d</h1>" % ((pg - 1) * PAGE_SIZE + 1, (pg - 1) * PAGE_SIZE + len(seg))
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
        h += "</table></div></body></html>"
        with open(os.path.join(ROOT, "pairs-static-%d.html" % pg), "w", encoding="utf-8") as f:
            f.write(h)
    print("pairs-index.html + %d static pages (%d pairs)" % (pages, len(pairs)))


if __name__ == "__main__":
    main()
