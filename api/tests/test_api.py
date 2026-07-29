from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.entities import ConfidenceLevel, LegalStatus, Scandal, ScandalCategory, Source
from app.services.labels import status_label
from scrapers.verifier import score_confidence, verify_record


@pytest_asyncio.fixture
async def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        s = Scandal(
            public_id="PPCA-TEST-0001",
            title="Test alleged procurement irregularity",
            summary="Alleged irregular tender; for unit testing only. Not a real case.",
            start_date=date(2020, 1, 1),
            end_date=date(2021, 1, 1),
            province="Punjab",
            city="Lahore",
            latitude=31.5,
            longitude=74.3,
            institution="Test Department",
            category=ScandalCategory.PROCUREMENT,
            sector="Public works",
            amount_pkr=1_000_000,
            amount_usd=3500,
            amount_notes="test",
            current_legal_status=LegalStatus.ALLEGATION,
            confidence_score=ConfidenceLevel.MEDIUM,
        )
        session.add(s)
        await session.flush()
        session.add(
            Source(
                scandal_id=s.id,
                title="Source A",
                url="https://www.dawn.com/test-a",
                publisher="Dawn",
                source_type="newspaper",
                is_primary=False,
            )
        )
        session.add(
            Source(
                scandal_id=s.id,
                title="Source B",
                url="https://www.reuters.com/test-b",
                publisher="Reuters",
                source_type="newspaper",
                is_primary=False,
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


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_scandals(client):
    r = await client.get("/api/v1/scandals")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert data["items"][0]["public_id"] == "PPCA-TEST-0001"
    assert data["items"][0]["source_count"] == 2


@pytest.mark.asyncio
async def test_scandal_detail_and_status_label(client):
    r = await client.get("/api/v1/scandals/PPCA-TEST-0001")
    assert r.status_code == 200
    data = r.json()
    assert data["status_label"] == "Alleged"
    assert len(data["sources"]) == 2
    assert "does not imply guilt" in data["disclaimer"].lower()


@pytest.mark.asyncio
async def test_dashboard_stats(client):
    r = await client.get("/api/v1/stats/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert data["total_scandals"] >= 1
    assert data["total_estimated_pkr"] >= 1_000_000


@pytest.mark.asyncio
async def test_export_json(client):
    r = await client.get("/api/v1/export/json")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_search(client):
    r = await client.get("/api/v1/search", params={"q": "procurement"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_status_labels():
    assert status_label(LegalStatus.CONVICTION) == "Convicted"
    assert status_label(LegalStatus.ACQUITTAL) == "Acquitted"
    assert status_label(LegalStatus.INVESTIGATION) == "Under Investigation"


def test_verifier_requires_two_sources():
    ok, issues = verify_record({"title": "x", "summary": "y", "sources": []})
    assert not ok
    assert "requires_minimum_2_independent_sources" in issues


def test_verifier_confidence():
    record = {
        "title": "t",
        "summary": "s",
        "sources": [
            {"url": "https://www.dawn.com/a", "source_type": "newspaper"},
            {"url": "https://www.supremecourt.gov.pk/b", "source_type": "court", "is_primary": True},
            {"url": "https://www.reuters.com/c", "source_type": "newspaper"},
        ],
    }
    assert score_confidence(record) == "high"
