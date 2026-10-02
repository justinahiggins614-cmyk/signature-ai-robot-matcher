#!/usr/bin/env python3
"""Build sitemap.xml for the Signature AI Robot Matcher."""
import gzip, json, os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/"
TODAY = date.today().isoformat()

rows = json.load(gzip.open(os.path.join(ROOT, "data/index/pairs.idx.json.gz"), "rt"))
bodies = json.load(open(os.path.join(ROOT, "data/bodies.json")))

urls = [("", "1.0"), ("#/pairs", "0.8"), ("#/bodies", "0.8"), ("#/mix", "0.8")]
for r in rows:
    urls.append(("?pair=" + r[0], "0.6"))
for b in bodies:
    urls.append(("?body=" + b["id"], "0.6"))

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, pr in urls:
    out.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
               % (BASE, path, TODAY, pr))
out.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(out))
print("sitemap.xml: %d URLs" % len(urls))
