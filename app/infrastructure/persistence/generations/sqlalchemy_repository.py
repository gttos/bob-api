from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.application.ports.repository_ports import GenerationRepository
from app.domain.generations.entities import GenerationRequest, ImageVariant, GenerationMode, GenerationStatus
from app.infrastructure.persistence.models import GenerationRequestModel, ImageVariantModel

class SQLAlchemyGenerationRepository(GenerationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, request: GenerationRequest) -> GenerationRequest:
        model = await self.session.get(GenerationRequestModel, request.id)
        if model:
            # Update
            model.source_image_id = request.source_image_id
            model.mode = request.mode.value
            model.provider = request.provider
            model.preset = request.preset
            model.instructions = request.instructions
            model.status = request.status.value
            model.error_message = request.error_message
            model.prompt_final = request.prompt_final
            model.negative_prompt = request.negative_prompt
            model.model = request.model
            model.output_image_id = request.output_image_id
            model.output_variant_id = request.output_variant_id
            model.completed_at = request.completed_at
        else:
            # Create
            model = GenerationRequestModel(
                id=request.id,
                source_image_id=request.source_image_id,
                mode=request.mode.value,
                provider=request.provider,
                preset=request.preset,
                instructions=request.instructions,
                status=request.status.value,
                error_message=request.error_message,
                prompt_final=request.prompt_final,
                negative_prompt=request.negative_prompt,
                model=request.model,
                output_image_id=request.output_image_id,
                output_variant_id=request.output_variant_id,
                created_at=request.created_at,
                completed_at=request.completed_at
            )
            self.session.add(model)

        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, id: UUID) -> Optional[GenerationRequest]:
        model = await self.session.get(GenerationRequestModel, id)
        if not model:
            return None
        return self._to_entity(model)

    async def list_by_image(self, image_id: UUID, offset: int, limit: int) -> List[GenerationRequest]:
        query = select(GenerationRequestModel).where(
            GenerationRequestModel.source_image_id == image_id
        ).order_by(GenerationRequestModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_by_image(self, image_id: UUID) -> int:
        query = select(func.count()).select_from(GenerationRequestModel).where(
            GenerationRequestModel.source_image_id == image_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def save_variant(self, variant: ImageVariant) -> ImageVariant:
        model = await self.session.get(ImageVariantModel, variant.id)
        if model:
            model.source_image_id = variant.source_image_id
            model.generation_request_id = variant.generation_request_id
            model.image_asset_id = variant.image_asset_id
            model.version_number = variant.version_number
            model.label = variant.label
            model.provider = variant.provider
            model.model = variant.model
        else:
            model = ImageVariantModel(
                id=variant.id,
                source_image_id=variant.source_image_id,
                generation_request_id=variant.generation_request_id,
                image_asset_id=variant.image_asset_id,
                version_number=variant.version_number,
                label=variant.label,
                provider=variant.provider,
                model=variant.model,
                created_at=variant.created_at
            )
            self.session.add(model)

        await self.session.flush()
        await self.session.refresh(model)
        return self._variant_to_entity(model)

    async def get_next_version_number(self, source_image_id: UUID) -> int:
        query = select(func.max(ImageVariantModel.version_number)).where(
            ImageVariantModel.source_image_id == source_image_id
        )
        result = await self.session.execute(query)
        max_version = result.scalar_one_or_none()

        if max_version is None:
            return 1
        return max_version + 1

    def _to_entity(self, model: GenerationRequestModel) -> GenerationRequest:
        return GenerationRequest(
            id=model.id,
            source_image_id=model.source_image_id,
            mode=GenerationMode(model.mode),
            provider=model.provider,
            preset=model.preset,
            instructions=model.instructions,
            status=GenerationStatus(model.status),
            error_message=model.error_message,
            prompt_final=model.prompt_final,
            negative_prompt=model.negative_prompt,
            model=model.model,
            output_image_id=model.output_image_id,
            output_variant_id=model.output_variant_id,
            created_at=model.created_at,
            completed_at=model.completed_at
        )

    def _variant_to_entity(self, model: ImageVariantModel) -> ImageVariant:
        return ImageVariant(
            id=model.id,
            source_image_id=model.source_image_id,
            generation_request_id=model.generation_request_id,
            image_asset_id=model.image_asset_id,
            version_number=model.version_number,
            label=model.label,
            provider=model.provider,
            model=model.model,
            created_at=model.created_at
        )
