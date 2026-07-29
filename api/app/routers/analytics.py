from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import stats as stats_service
from app.services.labels import DISCLAIMER

router = APIRouter()


@router.get("/trends")
async def trends(db: AsyncSession = Depends(get_db)):
    stats = await stats_service.dashboard_stats(db)
    money = await stats_service.money_by_year(db)
    duration = await stats_service.investigation_duration(db)
    return {
        "by_year": stats.by_year,
        "money_by_year": money,
        "by_institution": stats.by_institution,
        "by_category": stats.by_category,
        "by_status": stats.by_status,
        "conviction_stats": stats.conviction_stats,
        "investigation_duration": duration[:30],
        "disclaimer": DISCLAIMER,
    }


@router.get("/sankey")
async def sankey(db: AsyncSession = Depends(get_db)):
    data = await stats_service.sankey_money_flow(db)
    return {**data, "disclaimer": "Flows use documented alleged/reported amounts only."}
