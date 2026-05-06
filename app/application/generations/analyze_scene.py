from uuid import UUID
from typing import Optional

from app.domain.generations.entities import SceneInventory
from app.application.ports.repository_ports import SceneInventoryRepository, ImageRepository
from app.application.ports.task_queue_port import TaskQueuePort
from app.domain.shared.exceptions import ResourceNotFoundError

class AnalyzeSceneUseCase:
    def __init__(
        self,
        scene_repo: SceneInventoryRepository,
        image_repo: ImageRepository,
        task_queue: TaskQueuePort
    ):
        self.scene_repo = scene_repo
        self.image_repo = image_repo
        self.task_queue = task_queue

    async def execute(self, image_id: UUID, correlation_id: Optional[str] = None) -> SceneInventory:
        image = await self.image_repo.get_by_id(image_id)
        if not image:
            raise ResourceNotFoundError(f"Image {image_id} not found")

        inventory = SceneInventory(image_id=image_id, status="pending")
        saved_inventory = await self.scene_repo.save(inventory)

        await self.task_queue.enqueue(
            "app.infrastructure.tasks.celery_tasks.analyze_scene",
            str(image_id),
            correlation_id=correlation_id
        )

        return saved_inventory
