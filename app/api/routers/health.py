from fastapi import APIRouter
from pydantic import BaseModel
from app.config.settings import settings

router = APIRouter(tags=["health"])

class HealthResponse(BaseModel):
    status: str
    env: str
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        env=settings.APP_ENV,
        version="1.0.0"
    )
