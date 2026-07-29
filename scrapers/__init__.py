"""
OSINT scraping pipeline — robots.txt compliant, rate-limited, logged.

Allowed source classes only:
  government, court, major newspapers, intl orgs, academic/audit reports.
Never scrape: social media rumors, blogs, anonymous forums, propaganda sites.
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("ppca.scrapers")

ALLOWED_DOMAINS = {
    # Government / courts
    "nab.gov.pk",
    "ecp.gov.pk",
    "agp.gov.pk",
    "ppra.org.pk",
    "supremecourt.gov.pk",
    "fbr.gov.pk",
    "na.gov.pk",
    "senate.gov.pk",
    # Newspapers
    "dawn.com",
    "www.dawn.com",
    "thenews.com.pk",
    "www.thenews.com.pk",
    "tribune.com.pk",
    "brecorder.com",
    "www.brecorder.com",
    # International
    "reuters.com",
    "www.reuters.com",
    "apnews.com",
    "bbc.com",
    "www.bbc.com",
    "aljazeera.com",
    "www.aljazeera.com",
    "icij.org",
    "www.icij.org",
    "occrp.org",
    "www.occrp.org",
    "transparency.org",
    "www.transparency.org",
    "transparency.org.pk",
    "www.transparency.org.pk",
    "worldbank.org",
    "www.worldbank.org",
    "imf.org",
    "www.imf.org",
}

BLOCKED_DOMAIN_HINTS = (
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "medium.com",
    "blogspot.",
    "wordpress.com",
    "telegram.",
    "whatsapp.",
)


@dataclass
class FetchResult:
    url: str
    status_code: int
    content: str
    content_hash: str
    fetched_at: datetime
    from_cache: bool = False
    error: Optional[str] = None


@dataclass
class PipelineConfig:
    user_agent: str = "PPCA-OSINT-ResearchBot/1.0 (+https://example.org/ppca; research; respectful)"
    requests_per_minute: int = 10
    cache: dict[str, FetchResult] = field(default_factory=dict)
    cache_ttl_seconds: int = 3600
    respect_robots: bool = True
    timeout: int = 30


class RateLimiter:
    def __init__(self, rpm: int):
        self.min_interval = 60.0 / max(rpm, 1)
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()


class RobotsCache:
    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._parsers:
            rp = RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
            except Exception as exc:  # noqa: BLE001
                logger.warning("robots.txt fetch failed for %s: %s — failing closed", base, exc)
                return False
            self._parsers[base] = rp
        return self._parsers[base].can_fetch(self.user_agent, url)


def is_allowed_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    full = urlparse(url).netloc.lower()
    if any(b in full for b in BLOCKED_DOMAIN_HINTS):
        return False
    # Accept exact or parent match against allowlist
    for allowed in ALLOWED_DOMAINS:
        allowed_clean = allowed.removeprefix("www.")
        if host == allowed_clean or host.endswith("." + allowed_clean):
            return True
    return False


class Fetcher:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.limiter = RateLimiter(self.config.requests_per_minute)
        self.robots = RobotsCache(self.config.user_agent)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

    def _cache_get(self, url: str) -> Optional[FetchResult]:
        item = self.config.cache.get(url)
        if not item:
            return None
        age = (datetime.now(timezone.utc) - item.fetched_at).total_seconds()
        if age > self.config.cache_ttl_seconds:
            return None
        item.from_cache = True
        return item

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    def _get(self, url: str) -> requests.Response:
        self.limiter.wait()
        resp = self.session.get(url, timeout=self.config.timeout)
        resp.raise_for_status()
        return resp

    def fetch(self, url: str) -> FetchResult:
        if not is_allowed_url(url):
            return FetchResult(
                url=url,
                status_code=0,
                content="",
                content_hash="",
                fetched_at=datetime.now(timezone.utc),
                error="domain_not_allowlisted",
            )
        if self.config.respect_robots and not self.robots.allowed(url):
            return FetchResult(
                url=url,
                status_code=0,
                content="",
                content_hash="",
                fetched_at=datetime.now(timezone.utc),
                error="robots_disallowed",
            )
        cached = self._cache_get(url)
        if cached:
            logger.info("cache hit %s", url)
            return cached
        try:
            resp = self._get(url)
            content = resp.text
            digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
            result = FetchResult(
                url=url,
                status_code=resp.status_code,
                content=content,
                content_hash=digest,
                fetched_at=datetime.now(timezone.utc),
            )
            self.config.cache[url] = result
            logger.info("fetched %s (%s bytes)", url, len(content))
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("fetch failed %s", url)
            return FetchResult(
                url=url,
                status_code=0,
                content="",
                content_hash="",
                fetched_at=datetime.now(timezone.utc),
                error=str(exc),
            )


@dataclass
class RawArticle:
    url: str
    title: str
    text: str
    publisher: str
    published_date: Optional[str] = None
    source_type: str = "newspaper"


class Pipeline:
    """Modular pipeline: fetch → parse → clean → verify → upsert."""

    def __init__(
        self,
        fetcher: Optional[Fetcher] = None,
        parse_fn: Optional[Callable[[FetchResult], Optional[RawArticle]]] = None,
        clean_fn: Optional[Callable[[RawArticle], RawArticle]] = None,
        verify_fn: Optional[Callable[[dict[str, Any]], tuple[bool, list[str]]]] = None,
        upsert_fn: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.fetcher = fetcher or Fetcher()
        self.parse_fn = parse_fn
        self.clean_fn = clean_fn
        self.verify_fn = verify_fn
        self.upsert_fn = upsert_fn
        self.seen_hashes: set[str] = set()

    def run_urls(self, urls: list[str]) -> dict[str, Any]:
        stats = {"fetched": 0, "parsed": 0, "verified": 0, "upserted": 0, "errors": []}
        for url in urls:
            result = self.fetcher.fetch(url)
            if result.error:
                stats["errors"].append({"url": url, "error": result.error})
                continue
            if result.content_hash in self.seen_hashes:
                logger.info("dedupe skip %s", url)
                continue
            self.seen_hashes.add(result.content_hash)
            stats["fetched"] += 1

            if not self.parse_fn:
                continue
            article = self.parse_fn(result)
            if not article:
                continue
            stats["parsed"] += 1
            if self.clean_fn:
                article = self.clean_fn(article)

            record = {
                "title": article.title,
                "summary": article.text[:2000],
                "sources": [
                    {
                        "title": article.title,
                        "url": article.url,
                        "publisher": article.publisher,
                        "source_type": article.source_type,
                        "published_date": article.published_date,
                    }
                ],
                "content_hash": result.content_hash,
            }
            if self.verify_fn:
                ok, issues = self.verify_fn(record)
                if not ok:
                    stats["errors"].append({"url": url, "error": "verify_failed", "issues": issues})
                    continue
                stats["verified"] += 1
            if self.upsert_fn:
                self.upsert_fn(record)
                stats["upserted"] += 1
        return stats
