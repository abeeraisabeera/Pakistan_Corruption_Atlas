#!/usr/bin/env python3
"""Example scheduled update hook (cron / Task Scheduler / GitHub Actions)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scrapers import Fetcher, Pipeline, PipelineConfig
from scrapers.cleaner import clean_article
from scrapers.database import JsonlStore
from scrapers.parser import parse_with_newspaper
from scrapers.sources import all_seed_urls
from scrapers.verifier import verify_record

logging.basicConfig(level=logging.INFO)


def run_scheduled_update() -> int:
    out = ROOT / "data" / "staging" / f"candidates.jsonl"
    store = JsonlStore(out)
    pipeline = Pipeline(
        fetcher=Fetcher(PipelineConfig(requests_per_minute=4)),
        parse_fn=parse_with_newspaper,
        clean_fn=clean_article,
        verify_fn=verify_record,
        upsert_fn=store.upsert,
    )
    stats = pipeline.run_urls(all_seed_urls())
    logging.info("scheduled update finished: %s", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_scheduled_update())
