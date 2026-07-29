from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import stats as stats_service
from app.services.labels import DISCLAIMER

router = APIRouter()


@router.get("/graph")
async def network_graph(db: AsyncSession = Depends(get_db)):
    data = await stats_service.build_network(db)
    return {**data, "disclaimer": DISCLAIMER}
