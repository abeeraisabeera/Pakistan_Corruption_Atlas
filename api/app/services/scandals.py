"""Scandal query and serialization helpers."""
from __future__ import annotations

import math
import uuid
from typing import Optional

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    Individual,
    RelatedScandal,
    Scandal,
    ScandalIndividual,
    ScandalInstitution,
    Source,
)
from app.schemas.scandal import (
    DocumentOut,
    IndividualOut,
    InstitutionOut,
    PaginatedScandals,
    ScandalDetail,
    ScandalFilters,
    ScandalListItem,
    SourceOut,
    TimelineEventOut,
)
from app.services.labels import DISCLAIMER, status_label


async def _source_counts(session: AsyncSession, scandal_ids: list[str]) -> dict[str, int]:
    if not scandal_ids:
        return {}
    result = await session.execute(
        select(Source.scandal_id, func.count(Source.id))
        .where(Source.scandal_id.in_(scandal_ids))
        .group_by(Source.scandal_id)
    )
    return {row[0]: row[1] for row in result.all()}


def to_list_item(scandal: Scandal, source_count: int = 0) -> ScandalListItem:
    return ScandalListItem(
        id=scandal.id,
        public_id=scandal.public_id,
        title=scandal.title,
        summary=scandal.summary,
        start_date=scandal.start_date,
        end_date=scandal.end_date,
        province=scandal.province,
        city=scandal.city,
        latitude=scandal.latitude,
        longitude=scandal.longitude,
        institution=scandal.institution,
        category=scandal.category,
        sector=scandal.sector,
        amount_pkr=float(scandal.amount_pkr) if scandal.amount_pkr is not None else None,
        amount_usd=float(scandal.amount_usd) if scandal.amount_usd is not None else None,
        amount_notes=scandal.amount_notes,
        current_legal_status=scandal.current_legal_status,
        confidence_score=scandal.confidence_score,
        case_type=scandal.case_type,
        tags=list(scandal.tags or []),
        legal_outcome=scandal.legal_outcome,
        source_count=source_count,
        updated_at=scandal.updated_at,
    )


async def to_detail(session: AsyncSession, scandal: Scandal) -> ScandalDetail:
    counts = await _source_counts(session, [scandal.id])
    individuals: list[IndividualOut] = []
    for link in scandal.individuals:
        ind = link.individual
        individuals.append(
            IndividualOut(
                id=ind.id,
                full_name=ind.full_name,
                aliases=ind.aliases,
                political_party=ind.political_party,
                position_held=link.position_held,
                role_description=link.role_description,
            )
        )
    institutions: list[InstitutionOut] = []
    for link in scandal.institutions_rel:
        inst = link.institution
        institutions.append(
            InstitutionOut(
                id=inst.id,
                name=inst.name,
                type=inst.type,
                province=inst.province,
                relationship=link.relationship_type,
            )
        )
    related = await session.execute(
        select(RelatedScandal.related_id).where(RelatedScandal.scandal_id == scandal.id)
    )
    base = to_list_item(scandal, counts.get(scandal.id, 0))
    return ScandalDetail(
        **base.model_dump(),
        government_department=scandal.government_department,
        court_name=scandal.court_name,
        case_number=scandal.case_number,
        related_legislation=scandal.related_legislation or [],
        financial_loss_estimate=scandal.financial_loss_estimate,
        last_verified=scandal.last_verified,
        sources=[SourceOut.model_validate(s) for s in scandal.sources],
        timeline=[TimelineEventOut.model_validate(t) for t in scandal.timeline],
        documents=[DocumentOut.model_validate(d) for d in scandal.documents],
        individuals=individuals,
        institutions=institutions,
        related_scandal_ids=list(related.scalars().all()),
        status_label=status_label(scandal.current_legal_status),
        disclaimer=DISCLAIMER,
    )


def apply_filters(query, filters: ScandalFilters):
    clauses = [
        Scandal.is_published.is_(True),
        Scandal.deleted_at.is_(None),
    ]
    if filters.q:
        like = f"%{filters.q}%"
        clauses.append(
            or_(
                Scandal.title.ilike(like),
                Scandal.summary.ilike(like),
                Scandal.institution.ilike(like),
                Scandal.public_id.ilike(like),
                cast(Scandal.tags, String).ilike(like),
            )
        )
    if filters.province:
        clauses.append(Scandal.province == filters.province)
    if filters.city:
        clauses.append(Scandal.city.ilike(f"%{filters.city}%"))
    if filters.category:
        clauses.append(Scandal.category == filters.category)
    if filters.status:
        clauses.append(Scandal.current_legal_status == filters.status)
    if filters.case_type:
        clauses.append(Scandal.case_type == filters.case_type)
    if filters.tag:
        clauses.append(cast(Scandal.tags, String).ilike(f"%{filters.tag}%"))
    if filters.institution:
        clauses.append(Scandal.institution.ilike(f"%{filters.institution}%"))
    if filters.year_from:
        clauses.append(func.extract("year", Scandal.start_date) >= filters.year_from)
    if filters.year_to:
        clauses.append(func.extract("year", Scandal.start_date) <= filters.year_to)
    if filters.amount_min_pkr is not None:
        clauses.append(Scandal.amount_pkr >= filters.amount_min_pkr)
    if filters.amount_max_pkr is not None:
        clauses.append(Scandal.amount_pkr <= filters.amount_max_pkr)
    if filters.confidence:
        clauses.append(Scandal.confidence_score == filters.confidence)
    if clauses:
        query = query.where(and_(*clauses))
    return query


async def list_scandals(session: AsyncSession, filters: ScandalFilters) -> PaginatedScandals:
    query = select(Scandal)
    if filters.individual:
        query = (
            query.join(ScandalIndividual)
            .join(Individual)
            .where(Individual.full_name.ilike(f"%{filters.individual}%"))
        )
    query = apply_filters(query, filters)
    count_q = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_q) or 0
    pages = max(1, math.ceil(total / filters.page_size))
    result = await session.execute(
        query.order_by(Scandal.start_date.desc())
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    rows = list(result.scalars().unique().all())
    counts = await _source_counts(session, [r.id for r in rows])
    items = [to_list_item(r, counts.get(r.id, 0)) for r in rows]
    return PaginatedScandals(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=pages,
    )


def _scandal_id_clause(public_or_uuid: str):
    """Match public_id always; only compare UUID column when the value is a UUID.

    Comparing a non-UUID string to Scandal.id makes Postgres raise DBAPIError
    (invalid input syntax for type uuid), which the frontend surfaces as a 404.
    """
    try:
        uuid.UUID(public_or_uuid)
    except ValueError:
        return Scandal.public_id == public_or_uuid
    return or_(Scandal.public_id == public_or_uuid, Scandal.id == public_or_uuid)


async def get_scandal(session: AsyncSession, public_or_uuid: str) -> Optional[ScandalDetail]:
    result = await session.execute(
        select(Scandal)
        .options(
            selectinload(Scandal.sources),
            selectinload(Scandal.timeline),
            selectinload(Scandal.documents),
            selectinload(Scandal.individuals).selectinload(ScandalIndividual.individual),
            selectinload(Scandal.institutions_rel).selectinload(ScandalInstitution.institution),
        )
        .where(
            _scandal_id_clause(public_or_uuid),
            Scandal.is_published.is_(True),
            Scandal.deleted_at.is_(None),
        )
    )
    scandal = result.scalar_one_or_none()
    if not scandal:
        return None
    return await to_detail(session, scandal)
