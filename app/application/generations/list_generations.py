from dataclasses import dataclass
from uuid import UUID
from typing import List

from app.domain.generations.entities import GenerationRequest
from app.application.ports.repository_ports import GenerationRepository

@dataclass
class PaginatedGenerationsResult:
    items: List[GenerationRequest]
    total: int

class ListGenerationsUseCase:
    def __init__(self, generation_repo: GenerationRepository):
        self.generation_repo = generation_repo

    async def execute(self, image_id: UUID, page: int = 1, page_size: int = 20) -> PaginatedGenerationsResult:
        offset = (page - 1) * page_size
        items = await self.generation_repo.list_by_image(image_id, offset, page_size)
        total = await self.generation_repo.count_by_image(image_id)

        return PaginatedGenerationsResult(items=items, total=total)
