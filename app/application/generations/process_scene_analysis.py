from uuid import UUID
from datetime import datetime, timezone
from typing import Protocol

from app.domain.generations.entities import SceneInventory
from app.application.ports.repository_ports import SceneInventoryRepository, ImageRepository
from app.application.ports.storage_port import StoragePort
from app.domain.shared.exceptions import ResourceNotFoundError

class AIProviderRegistryProtocol(Protocol):
    def get(self, name: str) -> "AIProviderPort":
        ...

class ProcessSceneAnalysisUseCase:
    def __init__(
        self,
        scene_repo: SceneInventoryRepository,
        image_repo: ImageRepository,
        storage: StoragePort,
        ai_provider_registry: AIProviderRegistryProtocol
    ):
        self.scene_repo = scene_repo
        self.image_repo = image_repo
        self.storage = storage
        self.ai_provider_registry = ai_provider_registry

    async def execute(self, image_id: UUID) -> None:
        inventory = await self.scene_repo.get_by_image_id(image_id)
        if not inventory:
            # Auto-create the SceneInventory record if it doesn't exist
            # (happens when triggered automatically from upload or generation)
            image = await self.image_repo.get_by_id(image_id)
            if not image:
                raise ResourceNotFoundError(f"Image {image_id} not found")
            inventory = SceneInventory(image_id=image_id, status="pending")
            inventory = await self.scene_repo.save(inventory)

        try:
            image = await self.image_repo.get_by_id(image_id)
            if not image:
                raise ResourceNotFoundError(f"Image {image_id} not found")

            image_data = await self.storage.download(image.storage_path)

            # In MVP we only use OpenAI for analysis
            provider = self.ai_provider_registry.get("openai")

            analysis_result = await provider.analyze_scene(image_data)

            inventory.inventory_data = analysis_result.inventory
            inventory.provider = analysis_result.provider_name
            inventory.model = analysis_result.model_name
            inventory.status = "completed"
            inventory.completed_at = datetime.now(timezone.utc)

            await self.scene_repo.save(inventory)

        except Exception as e:
            inventory = await self.scene_repo.get_by_image_id(image_id)
            if inventory:
                inventory.status = "failed"
                inventory.error_message = str(e)
                inventory.completed_at = datetime.now(timezone.utc)
                await self.scene_repo.save(inventory)
            raise
