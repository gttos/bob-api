from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import redis.asyncio as redis

from app.infrastructure.persistence.database import get_session
from app.config.settings import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    db_status = "error"
    redis_status = "error"

    # Check DB
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        pass

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "ok"
        await r.close()
    except Exception:
        redis_status = "unavailable"

    status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": status,
        "env": settings.APP_ENV,
        "db": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }
