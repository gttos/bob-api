from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.application.stats.get_generation_stats import GetGenerationStatsUseCase
from app.api.dependencies import get_generation_stats_uc

router = APIRouter(prefix="/stats/generations", tags=["Stats"])

@router.get("")
async def get_generation_stats(
    group_by: str = Query("provider", description="Group by provider, project, or status"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    use_case: GetGenerationStatsUseCase = Depends(get_generation_stats_uc)
):
    return await use_case.execute(group_by=group_by, project_id=project_id)
