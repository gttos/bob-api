from uuid import UUID
from app.application.ports.repository_ports import SpaceRepository
from app.domain.shared.exceptions import ResourceNotFoundError

class DeleteSpaceUseCase:
    def __init__(self, space_repo: SpaceRepository):
        self.space_repo = space_repo

    async def execute(self, space_id: UUID) -> None:
        space = await self.space_repo.get_by_id(space_id)
        if not space:
            raise ResourceNotFoundError(f"Space with ID {space_id} not found")

        await self.space_repo.delete(space_id)
