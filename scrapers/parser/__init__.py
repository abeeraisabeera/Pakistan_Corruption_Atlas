"""HTML / article parsers using BeautifulSoup and optional newspaper3k."""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from scrapers import FetchResult, RawArticle

logger = logging.getLogger("ppca.parser")


def parse_generic_html(result: FetchResult, publisher: Optional[str] = None) -> Optional[RawArticle]:
    if not result.content:
        return None
    soup = BeautifulSoup(result.content, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or "Untitled"
    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text("\n", strip=True) if article else ""
    if len(text) < 200:
        logger.warning("thin content for %s", result.url)
        return None
    host = urlparse(result.url).netloc
    return RawArticle(
        url=result.url,
        title=title[:500],
        text=text,
        publisher=publisher or host,
        source_type=_infer_source_type(host),
    )


def parse_with_newspaper(result: FetchResult) -> Optional[RawArticle]:
    """Optional richer extraction when newspaper3k is installed."""
    try:
        from newspaper import Article
    except ImportError:
        return parse_generic_html(result)

    article = Article(result.url)
    article.set_html(result.content)
    article.parse()
    if not article.text or len(article.text) < 200:
        return parse_generic_html(result)
    host = urlparse(result.url).netloc
    published = article.publish_date.date().isoformat() if article.publish_date else None
    return RawArticle(
        url=result.url,
        title=(article.title or "Untitled")[:500],
        text=article.text,
        publisher=host,
        published_date=published,
        source_type=_infer_source_type(host),
    )


def _infer_source_type(host: str) -> str:
    host = host.lower()
    if any(x in host for x in ("gov.pk", "supremecourt", "ppra", "agp", "nab", "ecp", "fbr")):
        return "government"
    if any(x in host for x in ("icij", "occrp", "transparency", "worldbank", "imf")):
        return "intl_org"
    if "court" in host:
        return "court"
    return "newspaper"
