from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.scandal import DashboardStats
from app.services import stats as stats_service

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: AsyncSession = Depends(get_db)):
    return await stats_service.dashboard_stats(db)


@router.get("/map")
async def map_data(db: AsyncSession = Depends(get_db)):
    return {"points": await stats_service.map_points(db)}


@router.get("/money-by-year")
async def money_by_year(db: AsyncSession = Depends(get_db)):
    return {"series": await stats_service.money_by_year(db)}


@router.get("/investigation-duration")
async def investigation_duration(db: AsyncSession = Depends(get_db)):
    return {"items": await stats_service.investigation_duration(db)}
