from uuid import UUID

from app.domain.generations.entities import SceneInventory
from app.application.ports.repository_ports import SceneInventoryRepository
from app.domain.shared.exceptions import ResourceNotFoundError

class GetSceneInventoryUseCase:
    def __init__(self, scene_repo: SceneInventoryRepository):
        self.scene_repo = scene_repo

    async def execute(self, image_id: UUID) -> SceneInventory:
        inventory = await self.scene_repo.get_by_image_id(image_id)
        if not inventory:
            raise ResourceNotFoundError(f"Scene inventory for image {image_id} not found")
        return inventory
