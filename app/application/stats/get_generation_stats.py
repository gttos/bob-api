from uuid import UUID
from typing import Optional

from app.application.ports.repository_ports import GenerationRepository

class GetGenerationStatsUseCase:
    def __init__(self, generation_repo: GenerationRepository):
        self.generation_repo = generation_repo

    async def execute(self, group_by: str = "provider", project_id: Optional[UUID] = None) -> dict:
        # group_by could be "provider", "project", or "status"
        stats = await self.generation_repo.get_generation_stats(group_by, project_id)
        return stats
