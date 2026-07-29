"""Security hardening tests for the public-read API."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from app.models.entities import ConfidenceLevel, LegalStatus, Scandal, ScandalCategory, Source
from app.security.api_keys import reset_lockouts_for_tests, verify_api_key
from app.security.hashing import hash_secret, verify_secret
from app.middleware.rate_limit import reset_rate_limits_for_tests
from datetime import date


@pytest_asyncio.fixture
async def client(tmp_path):
    reset_rate_limits_for_tests()
    reset_lockouts_for_tests()
    db_path = tmp_path / "sec.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        s = Scandal(
            public_id="PPCA-SEC-0001",
            title="Security test alleged case",
            summary="Fixture for security tests only.",
            start_date=date(2020, 1, 1),
            province="Sindh",
            category=ScandalCategory.PROCUREMENT,
            current_legal_status=LegalStatus.ALLEGATION,
            confidence_score=ConfidenceLevel.MEDIUM,
            is_published=True,
        )
        draft = Scandal(
            public_id="PPCA-SEC-DRAFT",
            title="Unpublished draft",
            summary="Must not appear in public API.",
            start_date=date(2021, 1, 1),
            province="Sindh",
            category=ScandalCategory.BRIBERY,
            current_legal_status=LegalStatus.ALLEGATION,
            confidence_score=ConfidenceLevel.LOW,
            is_published=False,
        )
        session.add_all([s, draft])
        await session.flush()
        session.add(
            Source(
                scandal_id=s.id,
                title="A",
                url="https://www.dawn.com/a",
                publisher="Dawn",
                source_type="newspaper",
            )
        )
        session.add(
            Source(
                scandal_id=s.id,
                title="B",
                url="https://www.reuters.com/b",
                publisher="Reuters",
                source_type="newspaper",
            )
        )
        await session.commit()

    async def override_get_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()
    reset_lockouts_for_tests()
    reset_rate_limits_for_tests()


@pytest.mark.asyncio
async def test_security_headers_present(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "X-Request-ID" in r.headers
    assert "X-API-Version" in r.headers
    assert "X-RateLimit-Limit" in r.headers


@pytest.mark.asyncio
async def test_health_ready(client):
    r = await client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_validation_rejects_long_query(client):
    r = await client.get("/api/v1/search", params={"q": "x" * 201})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_validation_rejects_bad_year(client):
    r = await client.get("/api/v1/scandals", params={"year_from": 1900})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_unpublished_hidden(client):
    r = await client.get("/api/v1/scandals/PPCA-SEC-DRAFT")
    assert r.status_code == 404
    listed = await client.get("/api/v1/scandals")
    ids = [i["public_id"] for i in listed.json()["items"]]
    assert "PPCA-SEC-DRAFT" not in ids
    assert "PPCA-SEC-0001" in ids


@pytest.mark.asyncio
async def test_cors_allowlist(client):
    r = await client.options(
        "/api/v1/scandals",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"

    r2 = await client.get(
        "/api/v1/scandals",
        headers={"Origin": "https://evil.example"},
    )
    assert r2.headers.get("access-control-allow-origin") != "https://evil.example"


@pytest.mark.asyncio
async def test_rate_limit_export(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rate_limit_export", 3)
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    # Clear middleware buckets by creating many requests under low limit
    codes = []
    for _ in range(5):
        codes.append((await client.get("/api/v1/export/json")).status_code)
    assert 429 in codes


@pytest.mark.asyncio
async def test_injection_like_query_safe(client):
    r = await client.get("/api/v1/search", params={"q": "1'; DROP TABLE scandals;--"})
    assert r.status_code == 200
    # Still healthy
    assert (await client.get("/health")).status_code == 200


def test_argon2_hash_roundtrip():
    raw = "test-api-key-value-32chars-min!!"
    hashed = hash_secret(raw)
    assert verify_secret(raw, hashed)
    assert not verify_secret("wrong-key", hashed)


def test_api_key_verify(monkeypatch):
    raw = "staff-secret-key-abcdefgh"
    hashed = hash_secret(raw)
    from app.config import settings

    monkeypatch.setattr(settings, "api_key_hashes", [hashed])
    reset_lockouts_for_tests()
    assert verify_api_key(raw) is not None
    assert verify_api_key("nope") is None


def test_production_settings_disable_seed_and_sqlite():
    with pytest.raises(ValueError, match="USE_SQLITE"):
        Settings(environment="production", use_sqlite=True, seed_on_startup=True)

    s = Settings(
        environment="production",
        use_sqlite=False,
        database_url="postgresql+asyncpg://u:p@host/db?sslmode=require",
        seed_on_startup=True,
        disable_docs=None,
    )
    assert s.seed_on_startup is False
    assert s.docs_enabled is False


def test_docs_enabled_in_development():
    get_settings.cache_clear()
    s = Settings(environment="development", disable_docs=None)
    assert s.docs_enabled is True
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_export_json_ok(client):
    r = await client.get("/api/v1/export/json")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert all(item["public_id"] != "PPCA-SEC-DRAFT" for item in data["scandals"])
