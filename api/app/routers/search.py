from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.scandal import ScandalFilters
from app.services import scandals as scandal_service

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text style search across title, summary, institution, public_id."""
    page_size = min(page_size, settings.max_page_size)
    filters = ScandalFilters(q=q[: settings.max_query_length], page=page, page_size=page_size)
    result = await scandal_service.list_scandals(db, filters)
    return result
