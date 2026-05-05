from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.domain.generations.entities import GenerationRequest, ImageVariant, GenerationMode, GenerationStatus
from app.application.ports.storage_port import StoragePort

class GenerationRequestCreate(BaseModel):
    mode: str
    preset: Optional[str] = None
    instructions: Optional[str] = None
    provider: str = "openai"

class GenerationRequestResponse(BaseModel):
    id: UUID
    source_image_id: UUID
    mode: str
    preset: Optional[str] = None
    instructions: Optional[str] = None
    provider: str
    model: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    prompt_final: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, entity: GenerationRequest) -> "GenerationRequestResponse":
        return cls(
            id=entity.id,
            source_image_id=entity.source_image_id,
            mode=entity.mode.value,
            preset=entity.preset,
            instructions=entity.instructions,
            provider=entity.provider,
            model=entity.model,
            status=entity.status.value,
            error_message=entity.error_message,
            prompt_final=entity.prompt_final,
            created_at=entity.created_at,
            completed_at=entity.completed_at
        )

class ImageVariantResponse(BaseModel):
    id: UUID
    source_image_id: UUID
    version_number: int
    label: Optional[str] = None
    provider: str
    model: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    created_at: datetime

    # We pass image_asset_dict to resolve URLs
    @classmethod
    def from_entity(cls, variant: ImageVariant, storage_path: str, thumbnail_path: Optional[str], storage: StoragePort) -> "ImageVariantResponse":
        url = storage.get_url(storage_path) if storage_path else ""
        thumbnail_url = storage.get_url(thumbnail_path) if thumbnail_path else None

        return cls(
            id=variant.id,
            source_image_id=variant.source_image_id,
            version_number=variant.version_number,
            label=variant.label,
            provider=variant.provider,
            model=variant.model,
            url=url,
            thumbnail_url=thumbnail_url,
            created_at=variant.created_at
        )
