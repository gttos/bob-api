from dataclasses import dataclass
from uuid import UUID

from app.domain.images.entities import ImageAsset
from app.application.ports.repository_ports import ImageRepository


@dataclass
class ListImagesResult:
    items: list[ImageAsset]
    total: int


class ListImagesUseCase:
    def __init__(self, image_repo: ImageRepository):
        self.image_repo = image_repo

    async def execute(self, project_id: UUID, page: int = 1, page_size: int = 20) -> ListImagesResult:
        offset = (page - 1) * page_size

        items = await self.image_repo.list_by_project(
            project_id=project_id,
            offset=offset,
            limit=page_size
        )
        total = await self.image_repo.count_by_project(project_id)

        return ListImagesResult(items=items, total=total)
