from uuid import UUID
from app.domain.spaces.entities import Space
from app.application.ports.repository_ports import SpaceRepository

class ListSpacesUseCase:
    def __init__(self, space_repo: SpaceRepository):
        self.space_repo = space_repo

    async def execute(self, project_id: UUID) -> list[Space]:
        return await self.space_repo.list_by_project(project_id)
