from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.entities import ConfidenceLevel, LegalStatus, ScandalCategory
from app.schemas.scandal import PaginatedScandals, ScandalDetail, ScandalFilters
from app.services import scandals as scandal_service

router = APIRouter()


@router.get("", response_model=PaginatedScandals)
async def list_scandals(
    q: str | None = Query(None, max_length=200),
    province: str | None = Query(None, max_length=100),
    city: str | None = Query(None, max_length=100),
    category: ScandalCategory | None = None,
    status: LegalStatus | None = None,
    case_type: str | None = Query(None, max_length=100),
    tag: str | None = Query(None, max_length=100),
    institution: str | None = Query(None, max_length=300),
    individual: str | None = Query(None, max_length=300),
    year_from: int | None = Query(None, ge=1960, le=2026),
    year_to: int | None = Query(None, ge=1960, le=2026),
    amount_min_pkr: float | None = Query(None, ge=0),
    amount_max_pkr: float | None = Query(None, ge=0),
    confidence: ConfidenceLevel | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if page_size > settings.max_page_size:
        raise HTTPException(status_code=422, detail="page_size too large")
    if q and len(q) > settings.max_query_length:
        raise HTTPException(status_code=422, detail="q too long")

    filters = ScandalFilters(
        q=q,
        province=province,
        city=city,
        category=category,
        status=status,
        case_type=case_type,
        tag=tag,
        institution=institution,
        individual=individual,
        year_from=year_from,
        year_to=year_to,
        amount_min_pkr=amount_min_pkr,
        amount_max_pkr=amount_max_pkr,
        confidence=confidence,
        page=page,
        page_size=page_size,
    )
    return await scandal_service.list_scandals(db, filters)


@router.get("/{scandal_id}", response_model=ScandalDetail)
async def get_scandal(
    scandal_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[\w\-]+$"),
    db: AsyncSession = Depends(get_db),
):
    detail = await scandal_service.get_scandal(db, scandal_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Scandal not found")
    return detail
