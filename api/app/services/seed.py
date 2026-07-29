"""Seed / refresh database from ppca-export.json or legacy sample JSON."""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.entities import (
    ConfidenceLevel,
    Individual,
    Institution,
    LegalStatus,
    RelatedScandal,
    Scandal,
    ScandalCategory,
    ScandalIndividual,
    ScandalInstitution,
    Source,
    SupportingDocument,
    TimelineEvent,
)

logger = logging.getLogger(__name__)

CITY_COORDS: dict[tuple[str, str], tuple[float, float]] = {
    ("sindh", "karachi"): (24.8607, 67.0011),
    ("punjab", "lahore"): (31.5204, 74.3587),
    ("punjab", "rawalpindi"): (33.5651, 73.0169),
    ("punjab", "islamabad"): (33.6844, 73.0479),
    ("national", "islamabad"): (33.6844, 73.0479),
    ("khyber pakhtunkhwa", "peshawar"): (34.0151, 71.5249),
    ("khyber pakhtunkhwa", "swat"): (35.2227, 72.4258),
    ("balochistan", "quetta"): (30.1798, 66.9750),
}

PROVINCE_COORDS: dict[str, tuple[float, float]] = {
    "sindh": (25.8943, 68.5247),
    "punjab": (31.1704, 72.7097),
    "khyber pakhtunkhwa": (34.9526, 72.3311),
    "balochistan": (28.4907, 65.5906),
    "national": (33.6844, 73.0479),
    "islamabad": (33.6844, 73.0479),
}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def _coords(province: str | None, city: str | None) -> tuple[float | None, float | None]:
    p = (province or "").strip().lower()
    c = (city or "").strip().lower()
    if p and c and (p, c) in CITY_COORDS:
        return CITY_COORDS[(p, c)]
    # fuzzy city match
    for (pp, cc), coords in CITY_COORDS.items():
        if c and cc in c:
            return coords
        if c and c in cc:
            return coords
    if p in PROVINCE_COORDS:
        return PROVINCE_COORDS[p]
    return None, None


def _resolve_sample_path() -> Path:
    candidates = [
        Path(settings.sample_data_path),
        Path(__file__).resolve().parents[3] / "ppca-export.json",
        Path(__file__).resolve().parents[3] / "data" / "sample" / "scandals.json",
        Path("/data/sample/scandals.json"),
        Path("ppca-export.json"),
        Path("data/sample/scandals.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Sample/export data not found (ppca-export.json or scandals.json)")


def _normalize_timeline(raw_events: list) -> list[dict]:
    out = []
    for i, ev in enumerate(raw_events or []):
        if "event_date" in ev or "title" in ev:
            out.append(
                {
                    "event_date": ev.get("event_date"),
                    "title": ev.get("title") or ev.get("event") or "Event",
                    "description": ev.get("description"),
                    "status_at_event": ev.get("status_at_event"),
                    "source_url": ev.get("source_url") or ev.get("source"),
                    "sort_order": ev.get("sort_order", i),
                }
            )
        else:
            out.append(
                {
                    "event_date": ev.get("date"),
                    "title": (ev.get("event") or "Event")[:500],
                    "description": None,
                    "status_at_event": None,
                    "source_url": ev.get("source"),
                    "sort_order": i,
                }
            )
    return out


def _normalize_individuals(raw_people: list) -> list[dict]:
    out = []
    for person in raw_people or []:
        out.append(
            {
                "full_name": person.get("full_name") or person.get("name") or "Unnamed",
                "aliases": person.get("aliases") or [],
                "political_party": person.get("political_party") or person.get("party"),
                "notes": person.get("notes"),
                "position_held": person.get("position_held") or person.get("position"),
                "role_description": person.get("role_description"),
            }
        )
    return out


def _financial_from_raw(raw: dict) -> dict | None:
    fle = raw.get("financial_loss_estimate")
    if isinstance(fle, dict):
        return fle
    if raw.get("amount_pkr") is not None:
        return {
            "value": raw.get("amount_pkr"),
            "currency": "PKR",
            "confidence": raw.get("confidence_score", "medium"),
        }
    return None


async def _insert_scandal(session: AsyncSession, raw: dict) -> Scandal:
    lat = raw.get("latitude")
    lng = raw.get("longitude")
    if lat is None or lng is None:
        lat, lng = _coords(raw.get("province"), raw.get("city"))

    amount_pkr = raw.get("amount_pkr")
    fle = _financial_from_raw(raw)
    if amount_pkr is None and fle and fle.get("currency") == "PKR" and fle.get("value") is not None:
        amount_pkr = fle["value"]

    scandal = Scandal(
        public_id=raw["public_id"],
        title=raw["title"],
        summary=raw["summary"],
        start_date=_parse_date(raw["start_date"]),
        end_date=_parse_date(raw.get("end_date")),
        province=raw.get("province"),
        city=raw.get("city"),
        latitude=lat,
        longitude=lng,
        institution=raw.get("institution"),
        government_department=raw.get("government_department"),
        category=ScandalCategory(raw["category"]),
        sector=raw.get("sector"),
        amount_pkr=amount_pkr,
        amount_usd=raw.get("amount_usd"),
        amount_notes=raw.get("amount_notes"),
        current_legal_status=LegalStatus(raw["current_legal_status"]),
        court_name=raw.get("court_name"),
        case_number=raw.get("case_number"),
        related_legislation=raw.get("related_legislation") or [],
        confidence_score=ConfidenceLevel(raw.get("confidence_score", "medium")),
        case_type=raw.get("case_type"),
        tags=raw.get("tags") or [],
        financial_loss_estimate=fle,
        legal_outcome=raw.get("legal_outcome") or raw.get("status_label"),
        last_verified=_parse_date(raw.get("last_verified")),
        content_hash=raw.get("content_hash"),
    )
    session.add(scandal)
    await session.flush()

    for src in raw.get("sources", []):
        session.add(
            Source(
                scandal_id=scandal.id,
                title=src["title"],
                url=src["url"],
                publisher=src["publisher"],
                source_type=src["source_type"],
                published_date=_parse_date(src.get("published_date")),
                accessed_date=_parse_date(src.get("accessed_date")) or date.today(),
                quote_or_claim=src.get("quote_or_claim"),
                is_primary=bool(src.get("is_primary", False)),
            )
        )

    for ev in _normalize_timeline(raw.get("timeline") or []):
        if not ev.get("event_date"):
            continue
        status = None
        if ev.get("status_at_event"):
            try:
                status = LegalStatus(ev["status_at_event"])
            except ValueError:
                status = None
        session.add(
            TimelineEvent(
                scandal_id=scandal.id,
                event_date=_parse_date(ev["event_date"]),
                title=ev["title"],
                description=ev.get("description"),
                status_at_event=status,
                source_url=ev.get("source_url"),
                sort_order=ev.get("sort_order", 0),
            )
        )

    for doc in raw.get("documents", []):
        session.add(
            SupportingDocument(
                scandal_id=scandal.id,
                title=doc["title"],
                document_type=doc.get("document_type"),
                url=doc.get("url"),
                published_date=_parse_date(doc.get("published_date")),
            )
        )

    for person in _normalize_individuals(raw.get("individuals") or []):
        result = await session.execute(
            select(Individual).where(Individual.full_name == person["full_name"])
        )
        individual = result.scalar_one_or_none()
        if not individual:
            individual = Individual(
                full_name=person["full_name"],
                aliases=person.get("aliases") or [],
                political_party=person.get("political_party"),
                notes=person.get("notes"),
            )
            session.add(individual)
            await session.flush()
        session.add(
            ScandalIndividual(
                scandal_id=scandal.id,
                individual_id=individual.id,
                position_held=person.get("position_held"),
                role_description=person.get("role_description"),
            )
        )

    for inst in raw.get("institutions", []):
        name = inst if isinstance(inst, str) else inst["name"]
        result = await session.execute(select(Institution).where(Institution.name == name))
        institution = result.scalar_one_or_none()
        if not institution:
            institution = Institution(
                name=name,
                type=None if isinstance(inst, str) else inst.get("type"),
                province=None if isinstance(inst, str) else inst.get("province"),
            )
            session.add(institution)
            await session.flush()
        rel = None if isinstance(inst, str) else inst.get("relationship", "primary")
        session.add(
            ScandalInstitution(
                scandal_id=scandal.id,
                institution_id=institution.id,
                relationship_type=rel or "primary",
            )
        )

    # Derive a primary institution row from free-text institution when none provided
    if not raw.get("institutions") and raw.get("institution"):
        name = raw["institution"][:300]
        result = await session.execute(select(Institution).where(Institution.name == name))
        institution = result.scalar_one_or_none()
        if not institution:
            institution = Institution(name=name, type="primary", province=raw.get("province"))
            session.add(institution)
            await session.flush()
        session.add(
            ScandalInstitution(
                scandal_id=scandal.id,
                institution_id=institution.id,
                relationship_type="primary",
            )
        )

    return scandal


async def seed_if_empty(session: AsyncSession) -> int:
    """
    Load seed/export data.
    When replace_seed_on_startup is True, wipe scandals and reload.
    Otherwise insert any missing public_ids.
    """
    path = _resolve_sample_path()
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("scandals", payload)

    if settings.replace_seed_on_startup:
        await session.execute(delete(RelatedScandal))
        await session.execute(delete(Source))
        await session.execute(delete(TimelineEvent))
        await session.execute(delete(SupportingDocument))
        await session.execute(delete(ScandalIndividual))
        await session.execute(delete(ScandalInstitution))
        await session.execute(delete(Scandal))
        await session.commit()
        logger.info("Cleared existing scandals for full reseed from %s", path)

    existing = (await session.execute(select(Scandal.public_id, Scandal.id))).all()
    public_id_to_uuid: dict[str, str] = {pid: sid for pid, sid in existing}
    inserted = 0

    for raw in records:
        pid = raw["public_id"]
        if pid in public_id_to_uuid:
            continue
        scandal = await _insert_scandal(session, raw)
        public_id_to_uuid[pid] = scandal.id
        inserted += 1

    for raw in records:
        sid = public_id_to_uuid.get(raw["public_id"])
        for related_public_id in raw.get("related_scandal_ids") or []:
            rid = public_id_to_uuid.get(related_public_id)
            if not sid or not rid:
                continue
            found = await session.execute(
                select(RelatedScandal).where(
                    RelatedScandal.scandal_id == sid,
                    RelatedScandal.related_id == rid,
                )
            )
            if found.scalar_one_or_none():
                continue
            session.add(RelatedScandal(scandal_id=sid, related_id=rid, relationship="related"))

    await session.commit()
    logger.info("Seed complete from %s — inserted %s (total mapped %s)", path, inserted, len(public_id_to_uuid))
    return inserted
