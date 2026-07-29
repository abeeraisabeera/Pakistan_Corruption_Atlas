from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health():
    """Liveness — does not touch the database."""
    return {"status": "ok", "service": "ppca-api"}


@router.get("/health/ready")
async def ready(response: Response, db: AsyncSession = Depends(get_db)):
    """Readiness — verifies DB connectivity without leaking internals."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        response.status_code = 503
        return {"status": "not_ready"}
