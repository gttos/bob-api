from uuid import UUID
from typing import Protocol, Optional

from app.domain.generations.entities import GenerationStatus, ImageVariant
from app.domain.images.entities import ImageAsset
from app.domain.generations.services import PromptBuilder, PromptConfig, PromptResult
from app.application.ports.repository_ports import GenerationRepository, ImageRepository, SceneInventoryRepository
from app.application.ports.storage_port import StoragePort
from app.application.ports.task_queue_port import TaskQueuePort
from app.domain.shared.exceptions import ResourceNotFoundError

class AIProviderRegistryProtocol(Protocol):
    def get(self, name: str) -> "AIProviderPort":
        ...

class ThumbnailServiceProtocol(Protocol):
    def generate(self, image_data: bytes, max_size: tuple[int, int] = (400, 400)) -> bytes:
        ...

class PromptOptimizerProtocol(Protocol):
    async def optimize(self, mode: str, preset: str, user_instructions: str = "",
                       scene_inventory: Optional[dict] = None,
                       elements_to_remove: Optional[list[str]] = None) -> str:
        ...

class ProcessGenerationUseCase:
    def __init__(
        self,
        generation_repo: GenerationRepository,
        image_repo: ImageRepository,
        scene_inventory_repo: SceneInventoryRepository,
        storage: StoragePort,
        ai_provider_registry: AIProviderRegistryProtocol,
        prompt_builder: PromptBuilder,
        thumbnail_service: ThumbnailServiceProtocol,
        task_queue: Optional[TaskQueuePort] = None,
        prompt_optimizer: Optional[PromptOptimizerProtocol] = None,
    ):
        self.generation_repo = generation_repo
        self.image_repo = image_repo
        self.scene_inventory_repo = scene_inventory_repo
        self.storage = storage
        self.ai_provider_registry = ai_provider_registry
        self.prompt_builder = prompt_builder
        self.thumbnail_service = thumbnail_service
        self.task_queue = task_queue
        self.prompt_optimizer = prompt_optimizer

    async def execute(self, generation_request_id: UUID) -> None:
        try:
            request = await self.generation_repo.get_by_id(generation_request_id)
            if not request:
                raise ResourceNotFoundError(f"GenerationRequest {generation_request_id} not found")

            request.transition_to(GenerationStatus.analyzing)
            await self.generation_repo.save(request)

            source_image = await self.image_repo.get_by_id(request.source_image_id)
            if not source_image:
                raise ResourceNotFoundError(f"Source Image {request.source_image_id} not found")

            image_data = await self.storage.download(source_image.storage_path)

            # Get scene inventory for the source image (if available)
            scene_inventory_data = None
            scene_inv = await self.scene_inventory_repo.get_by_image_id(request.source_image_id)
            if scene_inv and scene_inv.status == "completed" and scene_inv.inventory_data:
                scene_inventory_data = scene_inv.inventory_data

            prompt_config = PromptConfig(
                mode=request.mode,
                provider=request.provider,
                preset=request.preset,
                user_instructions=request.instructions,
                scene_inventory=scene_inventory_data
            )

            # Use prompt optimizer (GPT-4o) if available, otherwise fallback to template
            if self.prompt_optimizer and scene_inventory_data:
                # Extract elements_to_remove from instructions if present
                elements_to_remove = None
                user_instructions = request.instructions or ""
                if "[REMOVE ELEMENTS:" in user_instructions:
                    parts = user_instructions.split("[REMOVE ELEMENTS:")
                    user_instructions = parts[0].strip()
                    remove_part = parts[1].rstrip("]").strip()
                    elements_to_remove = [e.strip() for e in remove_part.split(",") if e.strip()]

                optimized_prompt_text = await self.prompt_optimizer.optimize(
                    mode=request.mode.value,
                    preset=request.preset or request.mode.value,
                    user_instructions=user_instructions,
                    scene_inventory=scene_inventory_data,
                    elements_to_remove=elements_to_remove,
                )
                prompt_result = PromptResult(
                    prompt=optimized_prompt_text,
                    negative_prompt=None,
                    preservation_instructions=None,
                    provider_params=self.prompt_builder._get_provider_params(request.provider),
                )
            else:
                prompt_result = self.prompt_builder.build(prompt_config)

            request.transition_to(GenerationStatus.generating)
            await self.generation_repo.save(request)

            provider = self.ai_provider_registry.get(request.provider)
            generation_result = await provider.generate_variant(image_data, prompt_result)

            thumbnail_data = self.thumbnail_service.generate(
                generation_result.image_data, max_size=(400, 400)
            )

            # Storage paths
            storage_path = f"projects/{source_image.project_id}/generated/gen_{generation_request_id}.jpg"
            thumbnail_path = f"projects/{source_image.project_id}/generated/thumb_{generation_request_id}.jpg"

            await self.storage.upload(
                generation_result.image_data, storage_path, "image/jpeg"
            )
            await self.storage.upload(
                thumbnail_data, thumbnail_path, "image/jpeg"
            )

            new_image_asset = ImageAsset(
                project_id=source_image.project_id,
                type="generated",
                filename=f"gen_{generation_request_id}.jpg",
                mime_type="image/jpeg",
                width=1024,
                height=1024,
                storage_path=storage_path,
                thumbnail_path=thumbnail_path
            )
            saved_image_asset = await self.image_repo.save(new_image_asset)

            version_number = await self.generation_repo.get_next_version_number(source_image.id)

            image_variant = ImageVariant(
                source_image_id=source_image.id,
                generation_request_id=request.id,
                image_asset_id=saved_image_asset.id,
                version_number=version_number,
                provider=request.provider,
                model=generation_result.model_name
            )
            saved_variant = await self.generation_repo.save_variant(image_variant)

            request.prompt_final = prompt_result.prompt
            request.negative_prompt = prompt_result.negative_prompt
            request.model = generation_result.model_name
            request.output_image_id = saved_image_asset.id
            request.output_variant_id = saved_variant.id
            request.transition_to(GenerationStatus.completed)

            await self.generation_repo.save(request)

            # Auto-analyze the generated image for future iterations
            if self.task_queue:
                try:
                    await self.task_queue.enqueue(
                        "app.infrastructure.tasks.celery_tasks.analyze_scene",
                        str(saved_image_asset.id),
                    )
                except Exception:
                    pass  # Non-critical — don't fail the generation if analysis enqueue fails

        except Exception as e:
            request = await self.generation_repo.get_by_id(generation_request_id)
            if request:
                request.mark_failed(str(e))
                await self.generation_repo.save(request)
            raise
