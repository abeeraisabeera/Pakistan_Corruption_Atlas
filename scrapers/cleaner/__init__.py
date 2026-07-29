"""Normalize and clean scraped text fields."""
from __future__ import annotations

import re
import unicodedata

from scrapers import RawArticle

WHITESPACE_RE = re.compile(r"\s+")
BOILERPLATE_RE = re.compile(
    r"(share this|subscribe|advertisement|cookie policy|all rights reserved)",
    re.I,
)


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or BOILERPLATE_RE.search(line):
            continue
        lines.append(line)
    return WHITESPACE_RE.sub(" ", "\n".join(lines)).strip()


def clean_article(article: RawArticle) -> RawArticle:
    article.title = clean_text(article.title)[:500]
    article.text = clean_text(article.text)
    article.publisher = clean_text(article.publisher)[:300]
    return article
