#!/usr/bin/env python3
"""Build sitemaps for the Signature AI Robot Matcher.

  sitemap.xml          -> core pages + body deep links + static pair tables (back-compat)
  sitemap-pairs-N.xml  -> pair deep links (?pair=JAH-PAIR-######), 1000 per file
  sitemap-index.xml    -> index of the above
"""
import gzip
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-ai-robot-matcher/"
TODAY = date.today().isoformat()
BATCH = 1000


def doc(urls):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pr in urls:
        out.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                   % (BASE, path, TODAY, pr))
    out.append("</urlset>")
    return "\n".join(out)


def main():
    rows = json.load(gzip.open(os.path.join(ROOT, "data/index/pairs.idx.json.gz"), "rt"))
    bodies = json.load(open(os.path.join(ROOT, "data/bodies.json")))

    core = [("", "1.0"), ("#/pairs", "0.8"), ("#/bodies", "0.8"), ("#/mix", "0.8"),
            ("pairs-index.html", "0.8")]
    n = 1
    while True:
        if not os.path.exists(os.path.join(ROOT, "pairs-static-%d.html" % n)):
            break
        core.append(("pairs-static-%d.html" % n, "0.6"))
        n += 1
    for b in bodies:
        core.append(("?body=" + b["id"], "0.6"))
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(doc(core))

    pair_files = []
    for i in range(0, len(rows), BATCH):
        pg = i // BATCH + 1
        name = "sitemap-pairs-%d.xml" % pg
        urls = [("?pair=" + r[0], "0.6") for r in rows[i:i + BATCH]]
        open(os.path.join(ROOT, name), "w").write(doc(urls))
        pair_files.append(name)

    idx = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name in ["sitemap.xml"] + pair_files:
        idx.append("  <sitemap><loc>%s%s</loc><lastmod>%s</lastmod></sitemap>" % (BASE, name, TODAY))
    idx.append("</sitemapindex>")
    open(os.path.join(ROOT, "sitemap-index.xml"), "w").write("\n".join(idx))
    print("sitemap.xml (%d URLs) + %d pair sub-indexes + sitemap-index.xml" % (len(core), len(pair_files)))


if __name__ == "__main__":
    main()
