from uuid import UUID

from app.domain.images.entities import ImageAsset
from app.domain.shared.exceptions import ResourceNotFoundError
from app.application.ports.repository_ports import ImageRepository
from app.application.ports.storage_port import StoragePort


class GetImageUseCase:
    def __init__(self, image_repo: ImageRepository, storage: StoragePort):
        self.image_repo = image_repo
        self.storage = storage

    async def execute(self, image_id: UUID) -> ImageAsset:
        image = await self.image_repo.get_by_id(image_id)
        if not image:
            raise ResourceNotFoundError(f"Image with ID {image_id} not found")

        return image
