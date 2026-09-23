#!/usr/bin/env python3
"""Generate RSS, sitemap, robots.txt and a stable latest-briefing redirect."""
import argparse
from datetime import datetime, time, timezone, timedelta
from email.utils import format_datetime
from html import escape
import json
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE_URL = "https://gyu1718.github.io/newsgyu/"
KST = timezone(timedelta(hours=9))


def load_items():
    data = json.loads((ROOT / "data/briefings.json").read_text(encoding="utf-8"))
    items = list(data.get("briefings", []))
    items.sort(key=lambda item: item["date"], reverse=True)
    return items


def latest_html(items):
    if not items:
        target = "index.html"
        canonical = SITE_URL
        label = "브리핑 아카이브"
    else:
        target = f"briefings/{items[0]['date']}.html"
        canonical = SITE_URL + target
        label = f"최신 브리핑 {items[0]['date']}"
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escape(target, quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <title>{escape(label)} · 오전 8시 브리핑</title>
</head>
<body>
  <p><a href="{escape(target, quote=True)}">{escape(label)}로 이동</a></p>
</body>
</html>
'''


def rss_xml(items):
    rows = []
    for item in items[:30]:
        url = SITE_URL + f"briefings/{item['date']}.html"
        dt = datetime.combine(datetime.fromisoformat(item["date"]).date(), time(8, 0), KST)
        rows.append(f'''    <item>
      <title>{xml_escape(item['date'] + ' 오전 8시 브리핑')}</title>
      <link>{xml_escape(url)}</link>
      <guid isPermaLink="true">{xml_escape(url)}</guid>
      <pubDate>{format_datetime(dt)}</pubDate>
      <description>{xml_escape(item['summary'])}</description>
    </item>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>오전 8시 브리핑</title>
    <link>{SITE_URL}</link>
    <description>국제 증시, 국제사회, 국내, 캄보디아와 국제 개발협력 브리핑</description>
    <language>ko-KR</language>
{chr(10).join(rows)}
  </channel>
</rss>
'''


def load_threads():
    data = json.loads((ROOT / "data/threads.json").read_text(encoding="utf-8"))
    return list(data.get("threads", []))


def sitemap_xml(items):
    threads = load_threads()
    urls = (
        [SITE_URL]
        + [SITE_URL + f"briefings/{item['date']}.html" for item in items]
        + [SITE_URL + "threads/index.html"]
        + [SITE_URL + f"threads/{thread['id']}.html" for thread in threads]
    )
    body = "\n".join(f"  <url><loc>{xml_escape(url)}</loc></url>" for url in urls)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
'''


def outputs(items):
    return {
        DOCS / "latest.html": latest_html(items),
        DOCS / "rss.xml": rss_xml(items),
        DOCS / "sitemap.xml": sitemap_xml(items),
        DOCS / "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated extras without writing")
    args = parser.parse_args()
    files = outputs(load_items())
    differences = []
    for path, content in files.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                differences.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if differences:
        raise SystemExit("Generated site extras are stale: " + ", ".join(differences))
    print(f"{'Checked' if args.check else 'Built'} {len(files)} site extras.")


if __name__ == "__main__":
    main()
