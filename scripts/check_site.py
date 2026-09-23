#!/usr/bin/env python3
"""Catch missing local pages, assets and fragments before publishing."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1] / "docs"
BASE = "/newsforgyu/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.urls.append(attrs[attr])


def main():
    pages = {}
    for path in ROOT.rglob("*.html"):
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path] = parser
    errors = []
    for page, parser in pages.items():
        for url in parser.urls:
            parsed = urlparse(url)
            if parsed.scheme or parsed.netloc:
                continue
            route = unquote(parsed.path)
            if route.startswith(BASE):
                target = ROOT / route[len(BASE):]
            elif route.startswith("/"):
                errors.append(f"{page.name}: path escapes project site: {url}")
                continue
            else:
                target = (page.parent / route) if route else page
            target = target.resolve()
            if not target.is_relative_to(ROOT.resolve()):
                errors.append(f"{page.name}: path escapes docs: {url}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{page.name}: missing target: {url}")
            elif parsed.fragment and target.suffix == ".html":
                if unquote(parsed.fragment) not in pages[target].ids:
                    errors.append(f"{page.name}: missing fragment: {url}")
    if not pages or not (ROOT / "index.html").is_file() or not (ROOT / ".nojekyll").is_file():
        errors.append("Missing Pages entrypoint or .nojekyll")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Checked {len(pages)} HTML pages: local links, assets and fragments resolve.")


if __name__ == "__main__":
    main()
