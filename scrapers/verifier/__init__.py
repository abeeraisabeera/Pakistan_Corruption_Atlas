"""
Verification rules for OSINT records.

Minimum:
  - 2 independent reputable sources
  - citation for claims
  - confidence scoring
Never upgrade allegations to facts.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

REPUTABLE_PUBLISHERS = {
    "dawn",
    "the news",
    "express tribune",
    "business recorder",
    "reuters",
    "ap",
    "bbc",
    "al jazeera",
    "icij",
    "occrp",
    "transparency international",
    "transparency international pakistan",
    "world bank",
    "imf",
    "nab",
    "supreme court",
    "auditor general",
    "ppra",
    "election commission",
    "fbr",
}


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def score_confidence(record: dict[str, Any]) -> str:
    sources = record.get("sources") or []
    primary = sum(1 for s in sources if s.get("is_primary") or s.get("source_type") in ("government", "court"))
    independent_domains = {_domain(s["url"]) for s in sources if s.get("url")}
    if len(independent_domains) >= 3 and primary >= 1:
        return "high"
    if len(independent_domains) >= 2:
        return "medium"
    return "low"


def verify_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    sources = record.get("sources") or []
    if len(sources) < 2:
        issues.append("requires_minimum_2_independent_sources")
    domains = {_domain(s.get("url", "")) for s in sources}
    domains.discard("")
    if len(domains) < 2:
        issues.append("sources_must_be_independent_domains")
    if not record.get("title"):
        issues.append("missing_title")
    if not record.get("summary") and not record.get("title"):
        issues.append("missing_summary")
    status = record.get("current_legal_status")
    if status == "conviction" and not any(
        s.get("source_type") in ("court", "government") for s in sources
    ):
        issues.append("conviction_requires_court_or_government_source")
    # Language guard: discourage definitive guilt language without conviction status
    summary = (record.get("summary") or "").lower()
    if status not in ("conviction",) and any(
        phrase in summary for phrase in ("is guilty", "proven corrupt", "definitively stole")
    ):
        issues.append("summary_asserts_guilt_without_conviction_status")
    record["confidence_score"] = score_confidence(record)
    return (len(issues) == 0, issues)
