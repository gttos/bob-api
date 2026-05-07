from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from app.domain.generations.entities import GenerationRequest, GenerationMode, GenerationStatus
from app.application.ports.repository_ports import GenerationRepository, ImageRepository
from app.application.ports.task_queue_port import TaskQueuePort
from app.domain.shared.exceptions import ResourceNotFoundError

@dataclass
class RequestGenerationCommand:
    image_id: UUID
    mode: GenerationMode
    provider: str
    preset: Optional[str] = None
    instructions: Optional[str] = None
    elements_to_remove: Optional[list[str]] = None

class RequestGenerationUseCase:
    def __init__(
        self,
        generation_repo: GenerationRepository,
        image_repo: ImageRepository,
        task_queue: TaskQueuePort
    ):
        self.generation_repo = generation_repo
        self.image_repo = image_repo
        self.task_queue = task_queue

    async def execute(self, command: RequestGenerationCommand, correlation_id: Optional[str] = None) -> GenerationRequest:
        image = await self.image_repo.get_by_id(command.image_id)
        if not image:
            raise ResourceNotFoundError(f"Image with id {command.image_id} not found")

        request = GenerationRequest(
            source_image_id=command.image_id,
            mode=command.mode,
            provider=command.provider,
            preset=command.preset,
            instructions=command.instructions,
            status=GenerationStatus.pending
        )

        # Store elements_to_remove in the request for the worker to use
        if command.elements_to_remove:
            import json
            # Append to instructions so the worker can read it
            remove_text = ", ".join(command.elements_to_remove)
            if request.instructions:
                request.instructions += f"\n[REMOVE ELEMENTS: {remove_text}]"
            else:
                request.instructions = f"[REMOVE ELEMENTS: {remove_text}]"

        saved_request = await self.generation_repo.save(request)

        await self.task_queue.enqueue(
            "app.infrastructure.tasks.celery_tasks.process_generation",
            str(saved_request.id),
            correlation_id=correlation_id
        )

        return saved_request
