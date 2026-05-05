from dataclasses import dataclass
from uuid import UUID

from app.application.ports.repository_ports import ProjectRepository
from app.domain.projects.entities import Project
from app.domain.shared.exceptions import ResourceNotFoundError


@dataclass
class UpdateProjectCommand:
    project_id: UUID
    name: str | None = None
    description: str | None = None


class UpdateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, command: UpdateProjectCommand) -> Project:
        project = await self._project_repo.get_by_id(command.project_id)
        if project is None:
            raise ResourceNotFoundError(f"Project with ID {command.project_id} not found")

        project.update(name=command.name, description=command.description)
        return await self._project_repo.save(project)
