from dataclasses import dataclass

from app.application.ports.repository_ports import ProjectRepository
from app.domain.projects.entities import Project


@dataclass
class CreateProjectCommand:
    name: str
    description: str | None = None


class CreateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._project_repo = project_repo

    async def execute(self, command: CreateProjectCommand) -> Project:
        project = Project(
            name=command.name,
            description=command.description,
        )
        return await self._project_repo.save(project)
