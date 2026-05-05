from uuid import UUID

from app.application.ports.repository_ports import ProjectRepository
from app.domain.shared.exceptions import ResourceNotFoundError


class DeleteProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, project_id: UUID) -> None:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")

        await self._project_repo.delete(project_id)
