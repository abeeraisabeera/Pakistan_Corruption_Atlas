"""Source adapters — URL discovery only from allowlisted domains."""
from __future__ import annotations

# Seed discovery URLs for scheduled runs (expand per deployment).
SEED_URLS = {
    "agp": ["https://www.agp.gov.pk/"],
    "ppra": ["https://www.ppra.org.pk/"],
    "icij_panama": ["https://www.icij.org/investigations/panama-papers/"],
    "worldbank_sanctions": ["https://www.worldbank.org/en/about/unit/sanctions"],
    "transparency_pk": ["https://www.transparency.org.pk/"],
    "supreme_court": ["https://www.supremecourt.gov.pk/"],
}


def all_seed_urls() -> list[str]:
    urls: list[str] = []
    for group in SEED_URLS.values():
        urls.extend(group)
    return urls
