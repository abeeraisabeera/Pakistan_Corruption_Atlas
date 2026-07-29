#!/usr/bin/env python3
"""CLI entrypoint for scheduled OSINT updates."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scrapers import Fetcher, Pipeline, PipelineConfig
from scrapers.cleaner import clean_article
from scrapers.database import JsonlStore
from scrapers.parser import parse_with_newspaper
from scrapers.sources import all_seed_urls
from scrapers.verifier import verify_record

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="PPCA OSINT scrape pipeline")
    parser.add_argument("--url", action="append", dest="urls", help="URL to fetch (repeatable)")
    parser.add_argument("--seeds", action="store_true", help="Use built-in allowlisted seed URLs")
    parser.add_argument("--out", default="data/staging/candidates.jsonl")
    parser.add_argument("--rpm", type=int, default=6, help="Requests per minute")
    args = parser.parse_args()

    urls = list(args.urls or [])
    if args.seeds:
        urls.extend(all_seed_urls())
    if not urls:
        parser.error("Provide --url and/or --seeds")

    store = JsonlStore(args.out)
    pipeline = Pipeline(
        fetcher=Fetcher(PipelineConfig(requests_per_minute=args.rpm)),
        parse_fn=parse_with_newspaper,
        clean_fn=clean_article,
        verify_fn=verify_record,
        upsert_fn=store.upsert,
    )
    stats = pipeline.run_urls(urls)
    logging.info("pipeline complete: %s", stats)
    return 0 if not stats["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
