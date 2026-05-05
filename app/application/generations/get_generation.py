from uuid import UUID

from app.domain.generations.entities import GenerationRequest
from app.application.ports.repository_ports import GenerationRepository
from app.domain.shared.exceptions import ResourceNotFoundError

class GetGenerationUseCase:
    def __init__(self, generation_repo: GenerationRepository):
        self.generation_repo = generation_repo

    async def execute(self, generation_id: UUID) -> GenerationRequest:
        request = await self.generation_repo.get_by_id(generation_id)
        if not request:
            raise ResourceNotFoundError(f"Generation request with id {generation_id} not found")
        return request
