"""Extraction PDF depuis HTML."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class _PDFLinkParser(HTMLParser):
    """Parseur simple de liens PDF."""

    def __init__(self, add_url) -> None:
        super().__init__()
        self._add_url = add_url

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value for key, value in attrs if key}
        tag = tag.lower()
        if tag == "meta":
            name = (attrs_dict.get("name") or "").lower()
            if name == "citation_pdf_url":
                content = attrs_dict.get("content")
                if content:
                    self._add_url(content)
            return
        if tag == "a":
            href = attrs_dict.get("href")
            if href and ".pdf" in href.lower():
                self._add_url(href)


def extract_pdf_urls_from_html(html: str, base_url: str) -> list[str]:
    """Extrait des URLs PDF d un HTML."""
    urls: list[str] = []
    seen: set[str] = set()

    def _add(raw_url: str) -> None:
        if len(urls) >= 30:
            return
        if not raw_url:
            return
        absolute = urljoin(base_url, raw_url)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            return
        if absolute in seen:
            return
        seen.add(absolute)
        urls.append(absolute)

    parser = _PDFLinkParser(_add)
    try:
        parser.feed(html)
    except Exception:
        pass

    if len(urls) >= 30:
        return urls

    regex = re.compile(r"https?://[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?", re.I)
    for match in regex.findall(html):
        _add(match)
        if len(urls) >= 30:
            break

    return urls
