from dataclasses import dataclass
from uuid import UUID
from app.domain.spaces.entities import Space
from app.application.ports.repository_ports import SpaceRepository, ProjectRepository
from app.domain.shared.exceptions import ResourceNotFoundError

@dataclass
class CreateSpaceCommand:
    project_id: UUID
    name: str
    description: str | None = None

class CreateSpaceUseCase:
    def __init__(self, space_repo: SpaceRepository, project_repo: ProjectRepository):
        self.space_repo = space_repo
        self.project_repo = project_repo

    async def execute(self, command: CreateSpaceCommand) -> Space:
        # Verify project exists
        project = await self.project_repo.get_by_id(command.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {command.project_id} not found")

        space = Space(
            project_id=command.project_id,
            name=command.name,
            description=command.description
        )

        return await self.space_repo.save(space)
