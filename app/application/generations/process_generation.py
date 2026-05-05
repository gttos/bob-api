from uuid import UUID
from typing import Protocol

from app.domain.generations.entities import GenerationStatus, ImageVariant
from app.domain.images.entities import ImageAsset
from app.domain.generations.services import PromptBuilder, PromptConfig
from app.application.ports.repository_ports import GenerationRepository, ImageRepository
from app.application.ports.storage_port import StoragePort
from app.domain.shared.exceptions import ResourceNotFoundError

class AIProviderRegistryProtocol(Protocol):
    def get(self, name: str) -> "AIProviderPort":
        ...

class ThumbnailServiceProtocol(Protocol):
    def generate(self, image_data: bytes, max_size: tuple[int, int] = (400, 400)) -> bytes:
        ...

class ProcessGenerationUseCase:
    def __init__(
        self,
        generation_repo: GenerationRepository,
        image_repo: ImageRepository,
        storage: StoragePort,
        ai_provider_registry: AIProviderRegistryProtocol,
        prompt_builder: PromptBuilder,
        thumbnail_service: ThumbnailServiceProtocol
    ):
        self.generation_repo = generation_repo
        self.image_repo = image_repo
        self.storage = storage
        self.ai_provider_registry = ai_provider_registry
        self.prompt_builder = prompt_builder
        self.thumbnail_service = thumbnail_service

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

            # Scene inventory (Mocked for now since Phase 5 isn't complete)
            scene_inventory = None

            prompt_config = PromptConfig(
                mode=request.mode,
                provider=request.provider,
                preset=request.preset,
                user_instructions=request.instructions,
                scene_inventory=scene_inventory
            )
            prompt_result = self.prompt_builder.build(prompt_config)

            request.transition_to(GenerationStatus.generating)
            await self.generation_repo.save(request)

            provider = self.ai_provider_registry.get(request.provider)
            generation_result = await provider.generate_variant(image_data, prompt_result)

            thumbnail_data = self.thumbnail_service.generate(
                generation_result.image_data, max_size=(400, 400)
            )

            # Storage paths
            filename = f"gen_{generation_request_id}.jpg"
            thumb_filename = f"thumb_{generation_request_id}.jpg"
            project_id = str(source_image.project_id)

            storage_path = await self.storage.upload(
                generation_result.image_data, project_id, filename, "image/jpeg"
            )
            thumbnail_path = await self.storage.upload(
                thumbnail_data, project_id, thumb_filename, "image/jpeg"
            )

            # Need to get width/height somehow, mocking 1024x1024 for generated image
            new_image_asset = ImageAsset(
                project_id=source_image.project_id,
                type="generated",
                filename=filename,
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

        except Exception as e:
            # Need to re-fetch request if failed before getting it
            request = await self.generation_repo.get_by_id(generation_request_id)
            if request:
                request.mark_failed(str(e))
                await self.generation_repo.save(request)
            raise
