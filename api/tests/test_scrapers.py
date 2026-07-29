import pytest

from scrapers import is_allowed_url
from scrapers.cleaner import clean_text
from scrapers.verifier import verify_record


def test_allowlist_blocks_social():
    assert not is_allowed_url("https://twitter.com/rumor")
    assert not is_allowed_url("https://facebook.com/posts/1")
    assert is_allowed_url("https://www.dawn.com/news/123")
    assert is_allowed_url("https://www.supremecourt.gov.pk/judgement")


def test_clean_text_strips_boilerplate():
    text = "Real paragraph.\nShare this article\nMore facts."
    cleaned = clean_text(text)
    assert "Share this" not in cleaned
    assert "Real paragraph" in cleaned


def test_guilt_language_guard():
    ok, issues = verify_record(
        {
            "title": "Case",
            "summary": "Official is guilty of theft.",
            "current_legal_status": "allegation",
            "sources": [
                {"url": "https://www.dawn.com/a"},
                {"url": "https://www.reuters.com/b"},
            ],
        }
    )
    assert not ok
    assert "summary_asserts_guilt_without_conviction_status" in issues
