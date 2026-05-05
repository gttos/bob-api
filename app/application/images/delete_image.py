from uuid import UUID

from app.domain.shared.exceptions import ResourceNotFoundError
from app.application.ports.repository_ports import ImageRepository
from app.application.ports.storage_port import StoragePort


class DeleteImageUseCase:
    def __init__(self, image_repo: ImageRepository, storage: StoragePort):
        self.image_repo = image_repo
        self.storage = storage

    async def execute(self, image_id: UUID) -> None:
        # Get image from repo (raise ResourceNotFoundError if not found)
        image = await self.image_repo.get_by_id(image_id)
        if not image:
            raise ResourceNotFoundError(f"Image with ID {image_id} not found")

        # Delete file from storage (storage_path)
        if image.storage_path:
            try:
                await self.storage.delete(image.storage_path)
            except FileNotFoundError:
                pass # Ignore if already deleted

        # Delete thumbnail from storage (thumbnail_path) if exists
        if image.thumbnail_path:
            try:
                await self.storage.delete(image.thumbnail_path)
            except FileNotFoundError:
                pass # Ignore if already deleted

        # Delete from repository
        await self.image_repo.delete(image_id)
